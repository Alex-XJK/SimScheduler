import logging
from Schedulers.BaseScheduler import Scheduler
from Schedulers.FCFS_prefill import FCFSPre
from Schedulers.RR import RR
from Job import Job

class HybridFR(Scheduler):
    """
    A Hybrid Scheduler that combines First-Come-First-Serve for Prefill and Round-Robin for Decode.
    """
    def __init__(self, env, device, memory, chunk_size, chunk_time, collocate_threshold, time_slice=1):
        super().__init__(env, device, memory, 1,"Hybrid-FR")
        self.prefill_sched = FCFSPre(env, device, memory, chunk_size, chunk_time)
        self.decode_sched = RR(env, device, memory, collocate_threshold, time_slice)


    def add_job(self, job : Job) -> bool:
        """
        Override the add_job method to judge Job state and add to the correct scheduler.
        """
        if job.state == Job.State.INITIAL or job.state == Job.State.PREFILL:
            return self.prefill_sched.add_job(job)
        elif job.state == Job.State.DECODE:
            return self.decode_sched.add_job(job)
        else:
            raise ValueError(f"Job({job.job_id}) has an invalid state: {job.state}")

    def remove_job(self, job : Job):
        """
        Override the remove_job method to remove the job from the correct scheduler.
        """
        if job.state == Job.State.PREFILL:
            return self.prefill_sched.remove_job(job)
        elif job.state == Job.State.DECODE:
            return self.decode_sched.remove_job(job)
        else:
            raise ValueError(f"Job({job.job_id}) has an invalid state: {job.state}")

    def step(self) -> list[Job]:
        """
        Override the step method to handle collocation.
        """
        whole_list = []
        # Step the prefill scheduler
        logging.debug(f"{self.device.name} >> Executing Prefill Scheduler...")
        whole_list += self.prefill_sched.step()
        # Step the decode scheduler
        logging.debug(f"{self.device.name} >> Executing Decode Scheduler...")
        whole_list += self.decode_sched.step()
        return whole_list

    @property
    def num_jobs(self):
        """
        Override the num_jobs property to return the total number of jobs in both schedulers.
        """
        return self.prefill_sched.num_jobs + self.decode_sched.num_jobs

    def pick_movable_job(self, expected_stages: list[Job.State]) -> Job|None:
        """
        Override the pick_movable_job method to pick a job from different stages.
        """
        if Job.State.PREFILL in expected_stages:
            return self.prefill_sched.pick_movable_job(expected_stages)
        elif Job.State.DECODE in expected_stages:
            return self.decode_sched.pick_movable_job(expected_stages)
        else:
            return None

    def preempt_job(self, job : Job) -> bool:
        """
        Override the preempt_job method to preempt the job from the correct scheduler.
        """
        if job.state == Job.State.PREFILL or job.state == Job.State.INITIAL:
            return self.prefill_sched.preempt_job(job)
        elif job.state == Job.State.DECODE or job.state == Job.State.FINISHED:
            return self.decode_sched.preempt_job(job)
        else:
            raise ValueError(f"Job({job.job_id}) has an invalid state: {job.state}")

    def pick_next_task(self):
        pass

    def __str__(self):
        """
        Override the __str__ method to represent both schedulers.
        """
        return f"{self.name}:\n\t{self.prefill_sched}\n\t{self.decode_sched}"
