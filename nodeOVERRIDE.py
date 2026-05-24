import time
from asyncua.sync import Client

URL         = "opc.tcp://127.0.0.1:4840"
TEMP_TARGET = 295.0
STEP        = 2.0     # CalibrationOffset increase 
INTERVAL    = 30      # Allowing a time interval so the increase is gradual

NODE_IDS = (3, 4, 5, 6, 8, 9, 10, 12) # Node IDs identified from asyncuaCLI.py file

c = Client(URL)
c.connect()
nodes = {i: c.get_node(f"ns=2;i={i}") for i in NODE_IDS}

# Activate MAINTENANCE mode
print("Setting Mode = MAINTENANCE")
c.get_node("ns=2;i=12").write_value('MAINTENANCE')

# Enable test override
print("Setting TestOverride = True")
c.get_node("ns=2;i=13").write_value(True)

# ramp CalibrationOffset until Temperature >= 295
offset = nodes[6].read_value()
print(f"Starting offset ramp from {offset}")

try:
    while True:
        r = {i: nodes[i].read_value() for i in NODE_IDS}
        temp, raw, pressure, trip = r[4], r[3], r[5], r[10]
        print(f"offset={r[6]:6.1f}  Temp={temp:7.2f}  Raw={raw:7.2f}  "
              f"Pressure={pressure:6.2f}  Trip={trip}  Mode={r[12]}")

        if temp >= TEMP_TARGET:
            print(f">> Temp {temp:.2f} >= {TEMP_TARGET}, no trip — "
                  "maintenance window should be opening.")
            break

        offset += STEP
        nodes[6].write_value(offset)
        time.sleep(INTERVAL)
except KeyboardInterrupt:
    print("\nStopped at offset", offset)  # Allowing for KeyboardInterrupt in case temp reaches 295 prematurely
finally:
    try:
        c.disconnect()
    except Exception:
        pass