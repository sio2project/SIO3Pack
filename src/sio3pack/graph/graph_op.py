from sio3pack.graph.graph import Graph


class GraphOperation:
    """
    A class to represent a graph that should be run on workers.
    Allows for returning results.
    """

    def __init__(self, graph: Graph, return_results: bool = False, return_func: callable = None):
        """
        :param graph: The graph to run on workers.
        :param return_results: Whether to return the results.
        :param return_func: The function to use to return the
                            results, if return_results is True.
        """
        self.graph = graph
        self.should_return = return_results
        self.return_func = return_func

    def return_results(self, data: dict):
        if self.return_func and self.should_return:
            return self.return_func(data)
