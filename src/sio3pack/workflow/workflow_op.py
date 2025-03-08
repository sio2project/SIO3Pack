from sio3pack.workflow.workflow import Workflow


class WorkflowOperation:
    """
    A class to represent a workflow that should be run on workers.
    Allows for returning results.
    """

    def __init__(self, graph: Workflow, return_results: bool = False, return_func: callable = None):
        """
        :param graph: The workflow to run on workers.
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
