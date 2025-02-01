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

            # 3. Advance simulation time by 1 “second”
            yield self.env.timeout(1)

            # Check if we are done:
            all_generated = (self.generator.generated_count >= self.generator.total_limit)
            # Are there any unfinished jobs in the system?
            unfinished_jobs = any(not j.is_finished for j in self.scheduler.run_queue)
            if all_generated and not unfinished_jobs:
                print(f"All jobs completed by time {self.env.now}")
                break

        # End while
        print("Simulation ended at time", self.env.now)


    def report_stats(self):
        """
        Print or return some key metrics about job durations, wait times, etc.
        """
        all_jobs = self.completed_jobs
        # Could also gather incomplete jobs if the simulation ended early

        if not all_jobs:
            print("No jobs completed!")
            return

        total_times = [job.total_time_in_system for job in all_jobs]
        avg_ttis = sum(total_times) / len(total_times)
        max_ttis = max(total_times)
        print(f"Number of completed jobs: {len(all_jobs)}")
        print(f"Average time in system: {avg_ttis:.2f}")
        print(f"Tail time (max): {max_ttis:.2f}")


    def __str__(self):
        return "System"