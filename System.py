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

            # 2. Ask the scheduler who should run this step
            job_to_run = self.scheduler.step()

            if job_to_run:
                # If this job is just starting, record its start time
                if job_to_run.start_time is None:
                    job_to_run.start_time = self.env.now

                # Attempt to allocate memory if needed
                # If we haven't allocated its initial P tokens yet, do so:
                needed = job_to_run.current_size
                if needed > 0:
                    # Check if we already got memory or not
                    # (In a more detailed model, you might track how many tokens
                    #  a job has requested so far)
                    pass

                # For simplicity, assume the job has already allocated its P tokens
                # and each step we just try to allocate +1 token if it hasn't reached M
                if job_to_run.current_size < job_to_run.final_size:
                    additional_needed = 1
                    # Check if memory is available
                    if self.memory.available_tokens() >= additional_needed:
                        # "Grow" the job by 1 token
                        yield self.memory.request(additional_needed)
                        job_to_run.current_size += 1
                        # If job finished after this increment, mark finish time
                        if job_to_run.is_finished:
                            job_to_run.finish_time = self.env.now
                            self.completed_jobs.append(job_to_run)
                    else:
                        # Not enough memory to grow this job this step
                        pass
                else:
                    # If it's already at M, mark finish_time if not done
                    if job_to_run.finish_time is None:
                        job_to_run.finish_time = self.env.now
                        self.completed_jobs.append(job_to_run)

            # 3. Advance simulation time by 1 “second”
            yield self.env.timeout(1)

            # 4. Cleanup memory from jobs that have just finished
            #    We can free up all tokens for any job that finished at this time
            #    Because each job used P..M tokens over time, we might need to
            #    track how many tokens it was actually occupying.
            #    For simplicity, assume it was occupying job_to_run.current_size
            #    or final M if done.

            # Example memory cleanup:
            for j in self.completed_jobs:
                if j.finish_time == self.env.now:
                    # free all tokens job was using
                    yield self.memory.release(j.current_size)
                    # so it doesn't happen multiple times
                    j.current_size = 0

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