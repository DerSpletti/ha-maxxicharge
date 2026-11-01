"""Minimaler MQTT-Broker (Protokoll 3.1/3.1.1 und 5) für CCUs ohne vorhandenen Broker.

Bewusst klein gehalten: Benutzer/Passwort, Publish (QoS 0/1/2 eingehend), Subscribe mit
Wildcards, Retained-Nachrichten, Last Will, Keep-Alive. Ausgehend wird immer mit QoS 0
zugestellt (erlaubt, wenn QoS 0 gewährt wird). Keine HA-Importe, damit testbar.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import hmac
import logging
import secrets
import time
from typing import NamedTuple

_LOGGER = logging.getLogger(__name__)

MAX_PACKET = 1_048_576
MAX_CLIENTS = 20
MAX_RETAINED = 5000
CONNECT_TIMEOUT = 10


class Msg(NamedTuple):
    """Nachricht für interne Abonnenten (kompatibel zu HA ReceiveMessage: topic, payload)."""

    topic: str
    payload: str


def topic_matches(flt: str, topic: str) -> bool:
    """MQTT-Topic-Filter mit + und # prüfen."""
    if topic.startswith("$") and flt[:1] in ("+", "#"):
        return False
    f, t = flt.split("/"), topic.split("/")
    for i, part in enumerate(f):
        if part == "#":
            return True
        if i >= len(t):
            return False
        if part != "+" and part != t[i]:
            return False
    return len(f) == len(t)


def _enc_len(n: int) -> bytes:
    out = bytearray()
    while True:
        b, n = n % 128, n // 128
        out.append(b | 128 if n else b)
        if not n:
            return bytes(out)


def _packet(first: int, body: bytes) -> bytes:
    return bytes([first]) + _enc_len(len(body)) + body


def _enc_str(s: str) -> bytes:
    b = s.encode()
    return len(b).to_bytes(2, "big") + b


class _Reader:
    def __init__(self, data: bytes) -> None:
        self.data, self.pos = data, 0

    def remaining(self) -> int:
        return len(self.data) - self.pos

    def take(self, n: int) -> bytes:
        if n < 0 or self.pos + n > len(self.data):
            raise ValueError("Paket zu kurz")
        out = self.data[self.pos : self.pos + n]
        self.pos += n
        return out

    def u8(self) -> int:
        return self.take(1)[0]

    def u16(self) -> int:
        return int.from_bytes(self.take(2), "big")

    def bin(self) -> bytes:
        return self.take(self.u16())

    def str(self) -> str:
        return self.bin().decode("utf-8")

    def varint(self) -> int:
        mult, val = 1, 0
        for _ in range(4):
            b = self.u8()
            val += (b & 127) * mult
            mult *= 128
            if not b & 128:
                return val
        raise ValueError("Varint")

    def skip_props(self) -> None:
        self.take(self.varint())

    def rest(self) -> bytes:
        return self.take(self.remaining())


async def _read_packet(reader: asyncio.StreamReader, timeout: float | None) -> tuple[int, bytes]:
    first = (await asyncio.wait_for(reader.readexactly(1), timeout))[0]
    mult, length = 1, 0
    for _ in range(4):
        b = (await asyncio.wait_for(reader.readexactly(1), timeout))[0]
        length += (b & 127) * mult
        mult *= 128
        if not b & 128:
            break
    else:
        raise ValueError("Längenfeld")
    if length > MAX_PACKET:
        raise ValueError("Paket zu groß")
    body = await asyncio.wait_for(reader.readexactly(length), timeout) if length else b""
    return first, body


class _Client:
    def __init__(self, writer: asyncio.StreamWriter) -> None:
        self.writer = writer
        self.client_id = ""
        self.level = 4
        self.keepalive = 0
        self.subs: set[str] = set()
        self.will: tuple[str, bytes, bool] | None = None
        self.connected = False
        self.clean = False

    def send(self, data: bytes) -> None:
        if self.writer.is_closing():
            return
        if self.writer.transport.get_write_buffer_size() > 4_000_000:  # Client liest nicht mehr
            self.writer.close()
            return
        self.writer.write(data)


class MiniBroker:
    """Der Broker. Läuft im Event-Loop von Home Assistant."""

    def __init__(self, port: int, username: str, password: str, host: str = "0.0.0.0") -> None:
        self.port, self.username, self.password, self.host = port, username, password, host
        self._server: asyncio.Server | None = None
        self._clients: dict[str, _Client] = {}
        self._retained: dict[str, bytes] = {}
        self._internal: list[tuple[str, Callable[[Msg], None]]] = []
        self._rejected: dict[str, tuple[float, str]] = {}

    # ---------- Lebenszyklus ----------
    async def async_start(self) -> None:
        self._server = await asyncio.start_server(self._handle, self.host, self.port)
        _LOGGER.info("Eingebauter MQTT-Broker lauscht auf %s:%s", self.host, self.port)

    async def async_stop(self) -> None:
        if self._server is None:
            return
        self._server.close()
        for client in list(self._clients.values()):
            client.writer.close()
        try:
            async with asyncio.timeout(5):
                await self._server.wait_closed()
        except TimeoutError:
            pass
        self._server = None
        self._clients.clear()
        _LOGGER.info("Eingebauter MQTT-Broker gestoppt")

    def recent_rejections(self, window: float = 120.0) -> list[str]:
        """Clients, die sich zuletzt mit falschem Benutzer/Passwort angemeldet haben."""
        now = time.monotonic()
        return sorted(f"{c} ({why})" for c, (t, why) in self._rejected.items() if now - t <= window)

    # ---------- Interne API ----------
    def subscribe(self, flt: str, cb: Callable[[Msg], None]) -> Callable[[], None]:
        item = (flt, cb)
        self._internal.append(item)
        for topic, payload in list(self._retained.items()):
            if topic_matches(flt, topic):
                self._call(cb, Msg(topic, payload.decode("utf-8", "replace")))

        def _unsub() -> None:
            if item in self._internal:
                self._internal.remove(item)

        return _unsub

    def publish(self, topic: str, payload: str | bytes, retain: bool = False) -> None:
        data = payload.encode() if isinstance(payload, str) else payload
        self._route(topic, data, retain)

    @staticmethod
    def _call(cb: Callable[[Msg], None], msg: Msg) -> None:
        try:
            cb(msg)
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Fehler in internem MQTT-Abonnenten")

    # ---------- Routing ----------
    def _publish_packet(self, client: _Client, topic: str, payload: bytes, retain: bool) -> bytes:
        body = _enc_str(topic) + (b"\x00" if client.level == 5 else b"") + payload
        return _packet(0x30 | (1 if retain else 0), body)

    def _route(self, topic: str, payload: bytes, retain: bool) -> None:
        if retain:
            if payload:
                if topic in self._retained or len(self._retained) < MAX_RETAINED:
                    self._retained[topic] = payload
            else:
                self._retained.pop(topic, None)
        text = None
        for flt, cb in list(self._internal):
            if topic_matches(flt, topic):
                text = text if text is not None else payload.decode("utf-8", "replace")
                self._call(cb, Msg(topic, text))
        for client in list(self._clients.values()):
            if any(topic_matches(f, topic) for f in client.subs):
                client.send(self._publish_packet(client, topic, payload, False))

    # ---------- Verbindungen ----------
    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        client = _Client(writer)
        try:
            await self._session(client, reader)
        except (asyncio.IncompleteReadError, ConnectionError, TimeoutError, ValueError, OSError) as err:
            _LOGGER.debug("MQTT-Verbindung %s beendet: %r", client.client_id or "?", err)
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unerwarteter Fehler in MQTT-Verbindung")
        finally:
            self._drop(client)

    def _drop(self, client: _Client) -> None:
        if client.connected and self._clients.get(client.client_id) is client:
            del self._clients[client.client_id]
            if client.will and not client.clean:
                topic, payload, retain = client.will
                self._route(topic, payload, retain)
        client.connected = False
        client.writer.close()

    async def _session(self, client: _Client, reader: asyncio.StreamReader) -> None:
        first, body = await _read_packet(reader, CONNECT_TIMEOUT)
        if first >> 4 != 1 or not self._on_connect(client, body):
            return
        timeout = client.keepalive * 1.5 if client.keepalive else None
        while True:
            first, body = await _read_packet(reader, timeout)
            ptype = first >> 4
            if ptype == 3:
                self._on_publish(client, first, body)
            elif ptype == 8:
                self._on_subscribe(client, body)
            elif ptype == 10:
                self._on_unsubscribe(client, body)
            elif ptype == 12:
                client.send(b"\xd0\x00")
            elif ptype == 6:  # PUBREL -> PUBCOMP
                client.send(_packet(0x70, body[:2]))
            elif ptype == 14:
                client.clean = True
                return
            elif ptype not in (4, 5, 7):
                raise ValueError(f"Paketart {ptype} nicht unterstützt")

    def _refuse(self, client: _Client, v3_code: int, v5_code: int) -> None:
        if client.level == 5:
            client.send(_packet(0x20, bytes([0, v5_code, 0])))
        else:
            client.send(_packet(0x20, bytes([0, v3_code])))

    def _on_connect(self, client: _Client, body: bytes) -> bool:
        r = _Reader(body)
        name, level = r.str(), r.u8()
        client.level = level if level in (3, 4, 5) else 4
        if name not in ("MQTT", "MQIsdp") or level not in (3, 4, 5):
            self._refuse(client, 1, 0x84)
            return False
        flags, client.keepalive = r.u8(), r.u16()
        if level == 5:
            r.skip_props()
        cid = r.str() or f"auto-{secrets.token_hex(4)}"
        will = None
        if flags & 0x04:
            if level == 5:
                r.skip_props()
            wtopic, wpayload = r.str(), r.bin()
            will = (wtopic, wpayload, bool(flags & 0x20))
        user = r.bin() if flags & 0x80 else None
        pw = r.bin() if flags & 0x40 else None
        if self.username:
            user_ok = user is not None and hmac.compare_digest(user, self.username.encode())
            pw_ok = pw is not None and hmac.compare_digest(pw, self.password.encode())
            if not (user_ok and pw_ok):
                why = "user" if not user_ok else "password"
                self._rejected[cid] = (time.monotonic(), why)
                _LOGGER.warning(
                    "MQTT-Anmeldung abgelehnt von Client %s: %s stimmt nicht mit dem eingebauten Broker "
                    "überein (empfangener Benutzername: %r). In der Maxxisun-App Benutzer und Passwort "
                    "neu eintragen.",
                    cid,
                    "Benutzername" if why == "user" else "Passwort",
                    user.decode("utf-8", "replace")[:32] if user is not None else None,
                )
                self._refuse(client, 5, 0x87)
                return False
        if len(self._clients) >= MAX_CLIENTS and cid not in self._clients:
            self._refuse(client, 3, 0x88)
            return False
        old = self._clients.get(cid)
        if old is not None:
            old.will = None
            old.writer.close()
        client.client_id, client.will, client.connected = cid, will, True
        self._clients[cid] = client
        client.send(b"\x20\x03\x00\x00\x00" if level == 5 else b"\x20\x02\x00\x00")
        _LOGGER.debug("MQTT-Client %s verbunden (Protokoll %s)", cid, level)
        return True

    def _on_publish(self, client: _Client, first: int, body: bytes) -> None:
        qos, retain = (first >> 1) & 3, bool(first & 1)
        r = _Reader(body)
        topic = r.str()
        pid = r.u16() if qos else None
        if client.level == 5:
            r.skip_props()
        payload = r.rest()
        if not topic or "+" in topic or "#" in topic:
            raise ValueError("ungültiges Topic")
        if qos == 1:
            client.send(_packet(0x40, pid.to_bytes(2, "big")))
        elif qos == 2:
            client.send(_packet(0x50, pid.to_bytes(2, "big")))
        self._route(topic, payload, retain)

    def _on_subscribe(self, client: _Client, body: bytes) -> None:
        r = _Reader(body)
        pid = r.u16()
        if client.level == 5:
            r.skip_props()
        codes = bytearray()
        new: list[str] = []
        while r.remaining():
            flt, _opts = r.str(), r.u8()
            if flt:
                client.subs.add(flt)
                new.append(flt)
                codes.append(0)  # QoS 0 gewährt
            else:
                codes.append(0x8F if client.level == 5 else 0x80)
        client.send(
            _packet(0x90, pid.to_bytes(2, "big") + (b"\x00" if client.level == 5 else b"") + bytes(codes))
        )
        for flt in new:  # Retained-Nachrichten nachliefern
            for topic, payload in list(self._retained.items()):
                if topic_matches(flt, topic):
                    client.send(self._publish_packet(client, topic, payload, True))

    def _on_unsubscribe(self, client: _Client, body: bytes) -> None:
        r = _Reader(body)
        pid = r.u16()
        if client.level == 5:
            r.skip_props()
        count = 0
        while r.remaining():
            client.subs.discard(r.str())
            count += 1
        extra = b"\x00" + b"\x00" * count if client.level == 5 else b""
        client.send(_packet(0xB0, pid.to_bytes(2, "big") + extra))
