"""Test des Discovery-Parsers (Einzel- und Geräte-Discovery) ohne Home Assistant."""
import importlib.util
import json
import sys
import types

for m in ["homeassistant", "homeassistant.core"]:
    sys.modules[m] = types.ModuleType(m)
sys.modules["homeassistant.core"].callback = lambda f: f
pkg = types.ModuleType("mx"); pkg.__path__ = ["custom_components/maxxicharge"]; sys.modules["mx"] = pkg
def load(n):
    s = importlib.util.spec_from_file_location("mx." + n, f"custom_components/maxxicharge/{n}.py")
    m = importlib.util.module_from_spec(s); sys.modules["mx." + n] = m; s.loader.exec_module(m); return m
load("const"); d = load("discovery")
ID = "CCU2-B8F8-62C6-06E8"
res = {}

# Einzel-Discovery mit Abkürzungen und Basis-Topic
single = json.dumps({"~": "maxxi/x", "name": "Maximum Output", "uniq_id": ID + "_mp", "stat_t": "~/state",
                     "cmd_t": "~/set", "val_tpl": "{{ value_json.mp }}", "min": 0, "max": 2300,
                     "dev": {"ids": [ID], "name": ID, "mdl": "CCU Gen2"}})
sp = d.parse_message("homeassistant", f"homeassistant/number/{ID}/mp/config", single)
res["single"] = len(sp) == 1 and sp[0].command_topic == "maxxi/x/set" and sp[0].ccu_id == ID

# Geräte-Discovery mit gemeinsamem state_topic
device = json.dumps({"dev": {"ids": ID, "name": ID, "mf": "Maxxisun"}, "o": {"name": "ccu"},
                     "state_topic": "maxxi/x/state", "availability_topic": "maxxi/x/avail",
                     "cmps": {"mp": {"p": "number", "name": "Maximum Output", "unique_id": ID + "_mp",
                                     "command_topic": "maxxi/x/set/mp", "value_template": "{{ value_json.mp }}", "max": 2300},
                              "soc": {"p": "sensor", "name": "Local Battery SOC", "unique_id": ID + "_soc",
                                      "unit_of_measurement": "%"}}})
sp = d.parse_message("homeassistant", f"homeassistant/device/{ID}/config", device)
names = {s.name: s for s in sp}
res["device_two"] = set(names) == {"Maximum Output", "Local Battery SOC"}
res["device_shared_topic"] = names["Local Battery SOC"].state_topic == "maxxi/x/state"
res["device_command"] = names["Maximum Output"].command_topic == "maxxi/x/set/mp" and names["Maximum Output"].max == 2300.0
res["device_avail"] = names["Local Battery SOC"].availability_topic == "maxxi/x/avail"
res["unrelated_ignored"] = d.parse_message("homeassistant", "homeassistant/sensor/x/config", '{"name":"y","unique_id":"abc"}') == []
for k, v in res.items(): print("OK  " if v else "FAIL", k)
sys.exit(0 if all(res.values()) else 1)
