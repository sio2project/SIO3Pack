class WorkflowOperation:
    def __init__(
        self,
        get_workflow_func: callable,
        return_results=False,
        return_results_func: callable = None,
        *wf_args,
        **wf_kwargs
    ):
        self.get_workflow_func = get_workflow_func
        self.return_results = return_results
        self.return_results_func = return_results_func
        self._last = False
        self._data = None
        self._workflow = None
        self._workflow_args = wf_args
        self._workflow_kwargs = wf_kwargs

    def get_workflow(self):
        while not self._last:
            self._workflow, self._last = self.get_workflow_func(
                self._data, *self._workflow_args, **self._workflow_kwargs
            )
            yield self._workflow

    def return_results(self, data: dict):
        if self.return_results_func:
            return self.return_results_func(self._workflow, data)
        self._data = data
