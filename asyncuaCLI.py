from asyncua.sync import Client
from asyncua import ua
c = Client("opc.tcp://127.0.0.1:4840")
c.connect()
for i in range(1, 15):
    n = c.get_node(f"ns=2;i={i}")
    try:
        bn = n.read_browse_name().Name
        val = n.read_value()
        al = n.read_attribute(ua.AttributeIds.UserAccessLevel).Value.Value
        print(f"ns=2;i={i:<3} {bn:<20} value={val!r:<25} access={al}")
    except Exception as e:
        print(f"ns=2;i={i:<3} {bn:<20} (object/method) {e}")
c.disconnect()
