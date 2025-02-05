import simpy
import logging
from Generator import Generator
from Memory import Memory
from Scheduler import Scheduler


class System:
    """
    The main wrapper class for the system.
    """

    def __init__(self, env, memory : Memory, scheduler : Scheduler, generator : Generator):
        self.env = env
        # Create Memory
        self.memory = memory

        # Create concrete Scheduler
        self.scheduler = scheduler

        # Create Generator
        self.generator = generator

        # Bookkeeping for completed jobs
        self.completed_jobs = []


    def run_simulation(self, max_time=1000):
        while self.env.now < max_time:
            # 0. Print current time
            logging.debug(f"---------- Time: {self.env.now} ----------")

            # 1. Generate new jobs for this step
            self.generator.generate_jobs()

            # 2. Instruct the scheduler to run the next job
            current_job = self.scheduler.step()
            logging.debug(f"Scheduler picked job: {current_job}")

            # 3. Check if we are done:
            if self.generator.is_finished and self.scheduler.num_jobs == 0:
                logging.info(f"All jobs completed by time {self.env.now}")
                break

            # 4. Advance simulation time by 1 “second”
            yield self.env.timeout(1)

        # End while
        logging.info(f"Simulation ended at time {self.env.now}")
        self.completed_jobs = self.scheduler.finished_jobs


    def report_stats(self):
        print("---------- Simulation Results ----------")
        print("Total Time Elapsed:", self.env.now)
        print("Total Jobs Started:", self.generator.generated_count, ", Completed ", len(self.completed_jobs), " Remaining ", self.scheduler.num_jobs)

        if len(self.completed_jobs) == 0:
            print("No jobs completed!")
            return

        waiting_times = [job.start_time - job.arrival_time for job in self.completed_jobs]
        turnaround_times = [job.finish_time - job.arrival_time for job in self.completed_jobs]
        service_times = [job.finish_time - job.start_time for job in self.completed_jobs]

        average_waiting_time = sum(waiting_times) / len(waiting_times)
        average_turnaround_time = sum(turnaround_times) / len(turnaround_times)
        average_service_time = sum(service_times) / len(service_times)
        throughput = len(self.completed_jobs) / int(self.env.now)

        max_turnaround_time = max(turnaround_times)
        turnaround_times_sorted = sorted(turnaround_times)
        p95_index = int(0.95 * len(turnaround_times_sorted))
        p95_turnaround = turnaround_times_sorted[p95_index]

        # Compute slowdown for each job (avoid division by zero)
        slowdowns = [
            (tt / st) if st > 0 else 0
            for tt, st in zip(turnaround_times, service_times)
        ]
        average_slowdown = sum(slowdowns) / len(slowdowns)

        """
        Waiting Time    = [start - arrival]
        """
        print("Average Waiting Time:", average_waiting_time)

        """
        Turnaround Time = [finish - arrival]
        """
        print("Average Turnaround Time:", average_turnaround_time)
        print("Max Turnaround Time (Tail Latency):", max_turnaround_time)
        print("95th Percentile Turnaround Time:", p95_turnaround)

        """
        Service Time    = [finish - start]
        """
        print("Average Service Time:", average_service_time)

        """
        Throughput      = [jobs completed / total time]
        """
        print("Throughput:", throughput)

        """
        Slowdown        = [turnaround / service]
                        = [finish - arrival / finish - start]
        """
        print("Average Slowdown:", average_slowdown)


    def __str__(self):
        return "System Report:\n\t" + str(self.memory) + "\n\t" + str(self.generator) + "\n\t" + str(self.scheduler)