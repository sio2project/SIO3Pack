class WorkflowOperation:
    """
    A class to handle workflow operations, allowing for the retrieval of workflows
    and the return of results from those workflows.

    :param callable get_workflow_func: Function to retrieve workflows.
    :param bool return_results: Whether to return results from the workflow.
    :param callable return_results_func: Function to handle returning results.
    :param list[Any] wf_args: Additional positional arguments for the workflow function.
    :param dict[str, Any] wf_kwargs: Additional keyword arguments for the workflow function.
    """

    def __init__(
        self,
        get_workflow_func: callable,
        return_results: bool = False,
        return_results_func: callable = None,
        *wf_args,
        **wf_kwargs
    ):
        """
        Initialize the WorkflowOperation with a function to get workflows and
        optionally a function to return results.

        :param callable get_workflow_func: Function to retrieve workflows.
        :param bool return_results: Whether to return results from the workflow.
        :param callable return_results_func: Function to handle returning results.
        :param wf_args: Additional positional arguments for the workflow function.
        :param wf_kwargs: Additional keyword arguments for the workflow function.
        """
        self.get_workflow_func = get_workflow_func
        self.return_results = return_results
        self.return_results_func = return_results_func
        self._last = False
        self._data = None
        self._workflow = None
        self._workflow_args = wf_args
        self._workflow_kwargs = wf_kwargs

    def get_workflow(self):
        """
        A function to retrieve workflows. It yields workflows until the last one is reached.
        This function uses the provided `get_workflow_func` to get workflows and
        yields them one by one.
        """
        while not self._last:
            self._workflow, self._last = self.get_workflow_func(
                self._data, *self._workflow_args, **self._workflow_kwargs
            )
            yield self._workflow

    def return_results(self, data: dict):
        """
        A function to return results from the workflow. If `return_results_func` is provided,
        it will be called with the workflow and data. Also stores the data internally for next
        workflow retrieval.
        """
        if self.return_results_func:
            return self.return_results_func(self._workflow, data)
        self._data = data
