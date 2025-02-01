import simpy
import logging
from Memory import Memory
from Generator import Generator


class System:
    """
    The main wrapper class for the system.
    """

    def __init__(self, env, memory_capacity, scheduler_cls, scheduler_kwargs,
                 generator_kwargs):
        self.env = env
        # Create Memory
        self.memory = Memory(env, memory_capacity)

        # Create concrete Scheduler
        self.scheduler = scheduler_cls(env, self.memory, **scheduler_kwargs)

        # Create Generator
        self.generator = Generator(env, self.scheduler, **generator_kwargs)

        # Bookkeeping for completed jobs
        self.completed_jobs = []


    def run_simulation(self, max_time=1000):
        while self.env.now < max_time:
            # 0. Print current time
            logging.debug(f"---------- Time: {self.env.now} ----------")

            # 1. Generate new jobs for this step
            self.generator.generate_jobs()

            # 2. Instruct the scheduler to run the next job
            current_job = self.scheduler.pick_next_task()

            # 3. Check if we are done:
            if self.generator.is_finished and self.scheduler.num_jobs == 0:
                logging.info(f"All jobs completed by time {self.env.now}")
                break

            # 4. Advance simulation time by 1 “second”
            yield self.env.timeout(1)

        # End while
        logging.info("Simulation ended at time", self.env.now)
        self.completed_jobs = self.scheduler.finished_jobs
        self.report_stats()


    def report_stats(self):
        print("Simulation Results:")
        print(f"Total Time Elapsed: {self.env.now}")
        print(f"Total Jobs Started: {self.generator.generated_count}")
        print(f"Total Jobs Completed: {len(self.completed_jobs)}")
        print(f"Total Jobs Remaining: {self.scheduler.num_jobs}")


    def __str__(self):
        return "System Report:\n" + str(self.memory) + "\n" + str(self.scheduler) + "\n" + str(self.generator)