# Sicherheit

Sicherheitsprobleme bitte **nicht** öffentlich als Issue melden, sondern privat über GitHub:
**Security → Report a vulnerability** in diesem Repository.

Zur Einordnung:
- Die Integration arbeitet nur lokal (keine Cloud, keine Telemetrie).
- Der eingebaute MQTT-Broker verlangt Anmeldung, ist aber **nicht verschlüsselt**, wie die MQTT-Verbindung der CCU selbst. Er ist nur für das Heimnetz gedacht und gehört nicht ins Internet.
- Zugangsdaten stehen in der Konfiguration der Integration und werden im Diagnose-Download geschwärzt.
