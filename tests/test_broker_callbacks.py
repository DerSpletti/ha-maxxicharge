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
    attempt("ESP32_b", "maxxicharge", "Geheim123")      # Groß-/Kleinschreibung
    attempt("ESP32_c", "maxxicharge", " geheim123")     # Leerzeichen
    attempt("ESP32_d", "falsch", "geheim123")           # Benutzername
    attempt("ESP32_e", "maxxicharge", "ganzanders")     # Passwort

async def main():
    br = b.MiniBroker(PORT, "maxxicharge", "geheim123", "127.0.0.1")
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
    }
    for k, v in res.items(): print("OK  " if v else "FAIL", k)
    sys.exit(0 if all(res.values()) else 1)
asyncio.run(main())
