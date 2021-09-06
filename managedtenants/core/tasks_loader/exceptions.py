class PreTaskError(Exception):
    """
    Used when a pre task error happens
    """


class TaskFail(Exception):
    """
    Used when a task failire happens
    """


class TaskSkip(Exception):
    """
    Used when a task is skipped
    """


class PostTaskError(Exception):
    """
    Used when a post task error happens
    """
