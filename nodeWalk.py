from asyncua.sync import Client
c = Client("opc.tcp://127.0.0.1:4840") # Connection client
c.connect()

# Node walk to read all Node IDs 
def walk(node, d=0):
    try:
        bn = node.read_browse_name().Name
    except Exception:
        bn = "?"
    nc = node.read_node_class()
    print("  "*d, nc.name, node.nodeid.to_string(), bn)
    for ch in node.get_children():
        walk(ch, d+1)
walk(c.get_node("i=85"))   # start at Objects
c.disconnect()