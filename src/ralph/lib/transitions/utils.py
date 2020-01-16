class CycleError(Exception):
    pass


def _sort_graph_topologically(graph):
    """
    Sort directed graph topologicaly.

    Args:
        graph: dict of lists (key is node name, value if list of neighbours)

    Returns:
        generator of nodes in topoligical order
    """
    # calculate input degree (number of nodes pointing to particular node)
    indeg = {k: 0 for k in graph}
    for node, edges in graph.items():
        for edge in edges:
            indeg[edge] += 1
    # sort graph topologically
    # return nodes which input degree is 0
    no_requirements = set([a for a in indeg if indeg.get(a, 0) == 0])
    while no_requirements:
        next_node = no_requirements.pop()
        # for each node to which this one is pointing - decrease input degree
        for dependency in graph[next_node]:
            indeg[dependency] -= 1
            # add to set of nodes ready to be returned (without nodes pointing
            # to it)
            if indeg[dependency] == 0:
                no_requirements.add(dependency)
        yield next_node
    if any(indeg.values()):
        raise CycleError("Cycle detected during topological sort")


def _compare_instances_types(instances):
    """Function check type of instances.
    Conditions:
        - transition can run only objects with the same type.
    """
    if not all(
        map(lambda x: isinstance(instances[0], x.__class__), instances)
    ):
        raise TypeError()
