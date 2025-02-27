from Job import Job
from Generator import Generator

class RandomGenerator(Generator):
    """
    Creates new Jobs with random initial size and output size.
    - init_fn: function to generate initial size of a job.
    - output_fn: function to generate expected output size of a job.
    """
    def __init__(self, env, scheduler, speed, total, dropout, init_fn, output_fn):
        super().__init__(env, scheduler, speed, total, dropout, name="Random Generator")
        self.init_size_fn = init_fn
        self.output_size_fn = output_fn
        self.counter_init: list[int] = []
        self.counter_output: list[int] = []

    def try_add_one_job(self):
        """
        Try to add one job to the scheduler.
        Return True if successful, False otherwise.
        """
        arrival_time = self.env.now

        p = self.init_size_fn()
        m = self.output_size_fn()

        job = Job(job_id=self.job_id, arrival_time=arrival_time, init_size=p, expected_output=m)
        if self.scheduler.receive_job(job):
            self.counter_init.append(p)
            self.counter_output.append(m)
            return True
        return False

    def __str__(self):
        string = super().__str__() + "\t"
        if self.counter_init and self.counter_output:
            string += f"{min(self.counter_init)} ~ {max(self.counter_init)} initial size, "
            string += f"{min(self.counter_output)} ~ {max(self.counter_output)} output size."
        return string
