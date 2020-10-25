class Node(object):
    def __init__(self, type, *args):
        self.type = type
        self.args = args

    def __str__(self):
        s = "type: " + str(self.type) + "\n"
        s += "".join( ["i: " + str(i) + "\n" for i in self.args])
        return s
    #此函数用来打印node

def flatten(node, stop_node_type):
    if not isinstance(stop_node_type, list):
        stop_node_type = [stop_node_type]
    descending_leaves = []
    children = node.children
    for child in children:
        if isinstance(child, Node):
            if child.type in stop_node_type:
                descending_leaves.append(child)
            else:
                descending_leaves.extend(
                    flatten(child, stop_node_type))
        elif child is None:
            pass
        else:
            # reach the leaf node
            descending_leaves.append(child)
    return tuple(descending_leaves)