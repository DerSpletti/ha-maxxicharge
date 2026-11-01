"""Tests der Rechen- und Regellogik (ohne Home Assistant)."""
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("calc", "custom_components/maxxicharge/calc.py")
calc = importlib.util.module_from_spec(spec)
sys.modules["calc"] = calc
spec.loader.exec_module(calc)
res = {}

res["soc_weighted"] = calc.weighted_soc(3.432, 10.086) == 34.0
res["soc_none"] = calc.weighted_soc(None, 5) is None and calc.weighted_soc(1, 0) is None
res["house"] = calc.house_power(1180, 0, 498) == 682.0 and calc.house_power(None, 1, 1) is None
res["house_energy"] = calc.house_energy_today(5.0, 1.0, 2.0, 0.5) == 5.5
res["autarky"] = calc.autarky(2.0, 8.0) == 75.0 and calc.autarky(9, 8) == 0.0 and calc.autarky(1, 0.01) is None
res["self_consumption"] = calc.self_consumption(1.0, 4.0) == 75.0 and calc.self_consumption(1, 0.0) is None
res["efficiency"] = calc.efficiency(8.0, 10.0) == 80.0 and calc.efficiency(1, 0.5) is None
res["cycles"] = calc.cycles(100.0, 5.0) == 20.0
res["hours"] = calc.hours_left(2.0, 500) == 4.0 and calc.hours_left(2.0, 5) is None

res["dur_hours"] = calc.format_duration(80753) == "22 Std 25 Min"
res["dur_days"] = calc.format_duration(172975) == "2 Tage 0 Std 2 Min"
res["dur_one_day_en"] = calc.format_duration(90000, False) == "1 d 1 h 0 min"
res["dur_short"] = calc.format_duration(42) == "42 s" and calc.format_duration(None) is None

res["model_plus"] = calc.model_label("CCU2_PLUS") == "CCU V2+" and calc.model_label(" ccu2_plus ") == "CCU V2+"
res["model_v2"] = calc.model_label("CCU2") == "CCU V2"
res["model_unknown_is_v2"] = calc.model_label("UNKNOWN") == "CCU V2"
res["model_none"] = calc.model_label(None) is None and calc.model_label("") is None and calc.model_label("  ") is None

for k, v in res.items():
    print("OK  " if v else "FAIL", k)
sys.exit(0 if all(res.values()) else 1)
