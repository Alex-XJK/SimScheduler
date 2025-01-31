class Scheduler:
    """
    Base Scheduler class. Manages a queue/list of waiting jobs and
    picks which job runs next.
    """

    def __str__(self):
        return "Scheduler"