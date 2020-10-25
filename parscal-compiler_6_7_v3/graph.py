import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graphviz import Digraph
from ast import Node
from syntax import parse_grammar


def graph(node, filename):
    tree = traversal(node)
    g = Digraph("G", filename=filename, format='png', strict=False)
    first_label = list(tree.keys())[0]
    g.node("0", first_label)
    _sub_plot(g, tree, "0")
    g.view()

root = "0"

def _sub_plot(g, tree, inc):
    global root

    first_label = list(tree.keys())[0]
    ts = tree[first_label]
    for i in ts.keys():
        if isinstance(tree[first_label][i], dict):
            root = str(int(root) + 1)
            g.node(root, list(tree[first_label][i].keys())[0])
            g.edge(inc, root)
            _sub_plot(g, tree[first_label][i], root)
        else:
            root = str(int(root) + 1)
            g.node(root, tree[first_label][i])
            g.edge(inc, root)


def traversal(node):
    if node.__class__ != Node:
        return str(node)
    res = {node.type: {}}
    cnt = 0
    for c in node.args:
        # only Non-NoneType can be pictured in the graph
        if c:
            res[node.type].setdefault(cnt, traversal(c))
            cnt += 1
    return res

if __name__ == '__main__':
    if len(sys.argv) > 1:
        f = open(sys.argv[1], "r")
        data = f.read()
        f.close()
        result = parse_grammar(data)
        if len(sys.argv) > 2:
            graph(result, sys.argv[2])
        else:
            graph(result, "AST")
    else:
        data = ""
        while 1:
            try:
                data += input() + "\n"
            except:
                break
            if data == "q" or data == "quit":
                break
            if not data:
                continue

        result = parse_grammar(data)
        graph(result, "AST")