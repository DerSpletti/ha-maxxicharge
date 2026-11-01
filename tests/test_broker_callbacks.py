"""Rückrufe des Brokers: Ablehnung (mit Grund) und Verbindung."""
import asyncio, importlib.util, sys, threading, time
spec = importlib.util.spec_from_file_location("broker", "custom_components/maxxicharge/broker.py")
b = importlib.util.module_from_spec(spec); sys.modules["broker"] = b; spec.loader.exec_module(b)
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
PORT = 18832
events = []

def attempt(cid, user, pw):
    c = mqtt.Client(CallbackAPIVersion.VERSION2, client_id=cid); c.username_pw_set(user, pw)
    c.connect("127.0.0.1", PORT); c.loop_start(); time.sleep(0.7); c.loop_stop(); c.disconnect()

def run():
    attempt("ESP32_a", "maxxicharge", "geheim123")      # richtig
    attempt("ESP32_4379D8", "maxxicharge", "geheim123")  # Client-ID wie bei einer echten CCU
    attempt("ESP32_b", "maxxicharge", "Geheim123")      # Groß-/Kleinschreibung
    attempt("ESP32_c", "maxxicharge", " geheim123")     # Leerzeichen
    attempt("ESP32_d", "falsch", "geheim123")           # Benutzername
    attempt("ESP32_e", "maxxicharge", "ganzanders")     # Passwort
    c = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="ESP32_t"); c.username_pw_set("maxxicharge", "geheim123")
    c.connect("127.0.0.1", PORT); c.loop_start(); time.sleep(0.4)
    c.publish("maxxi/CCU/settings/result", '{"status":"applied"}').wait_for_publish(); time.sleep(0.4); c.loop_stop(); c.disconnect()

async def main():
    br = b.MiniBroker(PORT, "maxxicharge", "geheim123", "127.0.0.1")
    br.unknown_grace = 0  # im Test sofort melden
    connect_seen = []
    br.add_connect_listener(lambda cid: connect_seen.append(cid))
    br.on_reject = lambda cid, why: events.append(("reject", cid, why))
    br.on_connect = lambda cid: events.append(("connect", cid))
    await br.async_start()
    t = threading.Thread(target=run); t.start()
    while t.is_alive(): await asyncio.sleep(0.1)
    rej = br.recent_rejections()
    await br.async_stop()
    res = {
        "connect_cb": ("connect", "ESP32_a") in events,
        "case_hint": ("reject", "ESP32_b", "password: upper/lower case differs") in events,
        "space_hint": ("reject", "ESP32_c", "password: spaces at start/end") in events,
        "user_hint": ("reject", "ESP32_d", "user") in events,
        "password_hint": ("reject", "ESP32_e", "password") in events,
        "recent_list": len(rej) == 4,
        "listener_called": "ESP32_a" in connect_seen,
        "stat_client": (br.client_stat("CCU2-8045-6B43-79D8") or {}).get("client") == "ESP32_4379D8" and br.client_stat("CCU2-B8F8-62C6-06E8") is None,
        "key_function": b.ccu_client_key("CCU2-B8F8-62C6-06E8") == "C606E8" and b.client_matches("ESP32_c606E8", "CCU2-B8F8-62C6-06E8") and not b.client_matches("ESP32_4379D8", "CCU2-B8F8-62C6-06E8"),
        "stat_closed_reason": br.stats.get("ESP32_t", {}).get("closed") in ("DISCONNECT",) and br.stats["ESP32_t"]["last_publish"] is not None and br.stats["ESP32_t"]["connected"] is False,
        "unknown_topic": br.unknown_topics.get("maxxi/CCU/settings/result") == '{"status":"applied"}',
    }
    for k, v in res.items(): print("OK  " if v else "FAIL", k)
    sys.exit(0 if all(res.values()) else 1)
asyncio.run(main())
