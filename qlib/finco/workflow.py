import copy
from pathlib import Path

from qlib.log import get_module_logger
from qlib.finco.conf import Config
from qlib.finco.utils import parse_json
from qlib.finco.task import WorkflowTask, PlanTask, ActionTask, SummarizeTask

 
"""Context Manager stores the context of the workflow"""
"""All context are key value pairs which saves the input, output and status of the whole workflow"""
class WorkflowContextManager():
    def __init__(self) -> None:
        self.context = {}
        self.logger = get_module_logger("fincoWorkflowContextManager")

    def set_context(self, key, value):
        if key in self.context:
            self.logger.warning("The key already exists in the context, the value will be overwritten")
        self.context[key] = value
    
    def get_context(self, key):
        if key not in self.context:
            self.logger.warning("The key doesn't exist in the context")
            return None
        return self.context[key]
    
    """return a deep copy of the context"""
    """TODO: do we need to return a deep copy?"""
    def get_all_context(self):
        return copy.deepcopy(self.context)
    

class WorkflowManager:
    """This manange the whole task automation workflow including tasks and actions"""

    def __init__(self, name="project", output_path=None) -> None:

        if output_path is None:
            self._output_path = Path.cwd() / name
        else:
            self._output_path = Path(output_path)
        self._context = WorkflowContextManager()

    """Direct call set_context method of the context manager"""
    def set_context(self, key, value):
        self._context.set_context(key, value)

    def get_context(self) -> WorkflowContextManager:
        return self._context

    def run(self, prompt: str) -> Path:
        """
        The workflow manager is supposed to generate a codebase based on the prompt

        Parameters
        ----------
        prompt: str
            the prompt user gives

        Returns
        -------
        Path
            The workflow manager is expected to produce output that includes a codebase containing generated code, results, and reports in a designated location.
            The path is returned

            The output path should follow a specific format:
            - TODO: design
              There is a summarized report where user can start from.
        """

        # NOTE: The following items are not designed to make the workflow very flexible.
        # - The generated tasks can't be changed after geting new information from the execution retuls.
        #   - But it is required in some cases, if we want to build a external dataset, it maybe have to plan like autogpt...

        cfg = Config()

        # NOTE: list may not be enough for general task list
        self.set_context("user_prompt", prompt)
        task_list = [WorkflowTask()]
        while len(task_list):
            """task list is not long, so sort it is not a big problem"""
            """TODO: sort the task list based on the priority of the task"""
            # task_list = sorted(task_list, key=lambda x: x.task_type)
            t = task_list.pop(0)
            t.assign_context_manager(self._context)
            res = t.execute()
            if not cfg.continous_mode:
                res = t.interact()
            if isinstance(t, WorkflowTask) or isinstance(t, PlanTask):
                task_list.extend(res)
            elif isinstance(t, ActionTask):
                if res != "success":
                    ...
                    # TODO: handle the unexpected execution Error
            else:
                raise NotImplementedError("Unsupported action type")
            self.add_context(t.summarize())
        return self._output_path
