"""Task schema, loader and structural validator. See tasks/SCHEMA.md."""

from kilmeh.tasks.models import TaskSpec
from kilmeh.tasks.validate import validate_paths, validate_task_dir

__all__ = ["TaskSpec", "validate_paths", "validate_task_dir"]
