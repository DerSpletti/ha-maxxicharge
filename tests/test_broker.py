import asyncio
import importlib.util
import sys
import threading
import time

spec = importlib.util.spec_from_file_location("broker", "/home/agent/projekte/maxxicharge/custom_components/maxxicharge/broker.py")
b = importlib.util.module_from_spec(spec); sys.modules["broker"] = b; spec.loader.exec_module(b)
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

PORT = 18830
assert b.topic_matches("a/+/c", "a/x/c") and b.topic_matches("a/#", "a") and not b.topic_matches("+/x", "$sys/x")

def client(proto, user="u", pw="pw", cid="c", will=None):
    c = mqtt.Client(CallbackAPIVersion.VERSION2, client_id=cid, protocol=proto)
    c.username_pw_set(user, pw)
    if will: c.will_set(*will)
    c.got = []; c.rc = None
    c.on_connect = lambda cl, u, f, rc, p=None: setattr(c, "rc", rc)
    c.on_message = lambda cl, u, m: c.got.append((m.topic, m.payload.decode(), m.retain))
    return c

def run_clients(results):
    # Falscher Login
    bad = client(mqtt.MQTTv311, pw="falsch", cid="bad"); bad.connect("127.0.0.1", PORT); bad.loop_start(); time.sleep(1)
    results["bad_login_rejected"] = bad.rc is not None and getattr(bad.rc, "is_failure", bad.rc != 0)
    bad.loop_stop()
    for proto, name in ((mqtt.MQTTv311, "v311"), (mqtt.MQTTv5, "v5")):
        pub = client(proto, cid="ccu-"+name, will=("ccu/status", "offline", 0, True))
        pub.connect("127.0.0.1", PORT, keepalive=5); pub.loop_start(); time.sleep(0.5)
        pub.publish("homeassistant/number/CCU2-1/mp/config", '{"name":"x"}', qos=1, retain=True).wait_for_publish()
        pub.publish("ccu/status", "online", qos=0, retain=True).wait_for_publish()
        sub = client(proto, cid="sub-"+name); sub.connect("127.0.0.1", PORT); sub.loop_start(); time.sleep(0.5)
        sub.subscribe([("homeassistant/+/+/+/config", 0), ("ccu/#", 0), ("cmd/#", 0)]); time.sleep(0.8)
        pub.subscribe("cmd/#"); time.sleep(0.3)
        sub.publish("cmd/mp", "2200", qos=1).wait_for_publish(); time.sleep(0.5)
        pub.publish("ccu/state", '{"a":1}', qos=2).wait_for_publish(); time.sleep(0.5)
        results[name+"_retained_on_subscribe"] = ("homeassistant/number/CCU2-1/mp/config", '{"name":"x"}', True) in sub.got
        results[name+"_live_forward"] = ("ccu/state", '{"a":1}', False) in sub.got
        results[name+"_command_reaches_ccu"] = ("cmd/mp", "2200", False) in pub.got
        # Abbruch ohne DISCONNECT -> Last Will
        pub._sock.close(); time.sleep(1.0)
        results[name+"_will_after_crash"] = ("ccu/status", "offline", False) in sub.got
        sub.loop_stop(); pub.loop_stop(); sub.disconnect()

async def main():
    br = b.MiniBroker(PORT, "u", "pw", "127.0.0.1"); await br.async_start()
    internal = []
    br.subscribe("ccu/#", lambda m: internal.append(m))
    results = {}
    t = threading.Thread(target=run_clients, args=(results,)); t.start()
    while t.is_alive(): await asyncio.sleep(0.1)
    br.publish("cmd/internal", "x"); 
    results["internal_got_messages"] = any(m.topic == "ccu/state" for m in internal)
    await br.async_stop()
    for k, v in results.items(): print(("OK  " if v else "FAIL"), k)
    sys.exit(0 if all(results.values()) else 1)
asyncio.run(main())
