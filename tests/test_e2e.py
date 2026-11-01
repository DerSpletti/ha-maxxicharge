"""End-to-End: simulierte CCU meldet sich am eingebauten Broker, die Integration findet sie und ihr Befehl kommt an."""
import asyncio
import importlib.util
import json
import sys
import time
import types

for m in ["homeassistant","homeassistant.core"]:
    sys.modules[m]=types.ModuleType(m)
sys.modules["homeassistant.core"].callback=lambda f:f
pkg=types.ModuleType("mx"); pkg.__path__=["/home/agent/projekte/maxxicharge/custom_components/maxxicharge"]; sys.modules["mx"]=pkg
def load(n):
    s=importlib.util.spec_from_file_location("mx."+n,f"custom_components/maxxicharge/{n}.py"); m=importlib.util.module_from_spec(s); sys.modules["mx."+n]=m; s.loader.exec_module(m); return m
load("const"); broker=load("broker"); disc=load("discovery")
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion


class Bus:  # wie EmbeddedBus
    def __init__(s,b): s.b=b
    async def subscribe(s,t,cb): return s.b.subscribe(t,cb)
    async def publish(s,t,p,r=False): s.b.publish(t,p,r)

ID="CCU2-B8F8-62C6-06E8"
def ccu():
    c=mqtt.Client(CallbackAPIVersion.VERSION2, client_id=ID); c.username_pw_set("maxxicharge","geheim123")
    c.connect("127.0.0.1",18831); c.loop_start(); time.sleep(0.5)
    dev={"ids":[ID],"name":ID,"mf":"Maxxisun","mdl":"CCU Gen2"}
    c.publish(f"homeassistant/number/{ID}/mp/config", json.dumps({"name":"Maximum Output","uniq_id":ID+"_mp","stat_t":f"maxxi/{ID}/state","val_tpl":"{{ value_json.mp }}","cmd_t":f"maxxi/{ID}/set/mp","min":0,"max":2300,"unit_of_meas":"W","dev":dev}),retain=True)
    c.publish(f"homeassistant/sensor/{ID}/soc/config", json.dumps({"name":"Local Battery SOC","uniq_id":ID+"_soc","stat_t":f"maxxi/{ID}/state","unit_of_meas":"%","dev":dev}),retain=True)
    c.publish(f"maxxi/{ID}/state", '{"mp": 2300}', retain=True).wait_for_publish()
    return c

async def main():
    b=broker.MiniBroker(18831,"maxxicharge","geheim123","127.0.0.1"); await b.async_start()
    res={}
    c=await asyncio.get_running_loop().run_in_executor(None, ccu)
    found=await disc.async_collect(Bus(b),"homeassistant",None,5)
    res["ccu_found"]= ID in found
    sp=found.get(ID,{})
    res["two_entities"]=set(sp)=={"Maximum Output","Local Battery SOC"}
    res["topics"]= sp["Maximum Output"].command_topic==f"maxxi/{ID}/set/mp" and sp["Maximum Output"].max==2300.0
    # Cache-Roundtrip
    res["cache_roundtrip"]= disc.specs_from_json(json.loads(json.dumps(disc.specs_to_json(sp))))==sp
    # Befehl der Integration kommt an der CCU an
    got=[]; c.on_message=lambda cl,u,m: got.append((m.topic,m.payload.decode())); c.subscribe(f"maxxi/{ID}/set/#"); await asyncio.sleep(0.5)
    await Bus(b).publish(sp["Maximum Output"].command_topic,"2200"); await asyncio.sleep(0.5)
    res["command_delivered"]= (f"maxxi/{ID}/set/mp","2200") in got
    c.loop_stop(); await b.async_stop()
    for k,v in res.items(): print("OK  " if v else "FAIL",k)
    sys.exit(0 if all(res.values()) else 1)
asyncio.run(main())
