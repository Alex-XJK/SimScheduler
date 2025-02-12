import simpy
import logging
from dataclasses import dataclass

from Generator import Generator
from Memory import Memory
from Scheduler import Scheduler


@dataclass
class SysReport:
    # Job statistics
    total_time: int = 0
    finished_jobs: int = 0
    throughput: float = 0.0
    # Raw arrays
    waiting_times: list[int] = None
    turnaround_times: list[int] = None
    service_times: list[int] = None
    slowdowns: list[float] = None
    # Computed statistics
    average_waiting_time: float = 0.0
    average_turnaround_time: float = 0.0
    max_turnaround_time: float = 0.0
    p95_turnaround: float = 0.0
    average_service_time: float = 0.0
    average_slowdown: float = 0.0
    p95_slowdown: float = 0.0

    def __str__(self):
        return f"""
        -------------------- Simulation Results --------------------
        Total Time Elapsed: {self.total_time}
        Total Jobs Started: {self.finished_jobs}
        Throughput: {self.throughput:.10f}
        -------------------- Job Statistics --------------------
        Average Waiting Time: {self.average_waiting_time:.2f}
        Average Turnaround Time: {self.average_turnaround_time:.2f}
        Max Turnaround Time (Tail Latency): {self.max_turnaround_time:.2f}
        95th Percentile Turnaround Time: {self.p95_turnaround:.2f}
        Average Service Time: {self.average_service_time:.2f}
        Average Slowdown: {self.average_slowdown:.2f}
        95th Percentile Slowdown: {self.p95_slowdown:.2f}
        -------------------- End of Report --------------------
        """

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
            working_jobs = self.scheduler.step()
            for current_job in working_jobs:
                logging.debug(f"Scheduler Picked: {current_job}")

            # 3. Check if we are done:
            if self.generator.is_finished and self.scheduler.num_jobs == 0:
                logging.info(f"All jobs completed by time {self.env.now}")
                break

            # 4. Advance simulation time by 1 “second”
            yield self.env.timeout(1)

        # End while
        logging.info(f"Simulation ended at time {self.env.now}")
        self.completed_jobs = self.scheduler.finished_jobs


    def report_stats(self) -> SysReport:
        sysreport = SysReport()

        sysreport.total_time = self.env.now
        sysreport.finished_jobs = len(self.completed_jobs)

        if len(self.completed_jobs) == 0:
            return sysreport

        """
        Waiting Time    = [start - arrival]
        """
        waiting_times = [job.start_time - job.arrival_time for job in self.completed_jobs]
        sysreport.waiting_times = waiting_times

        average_waiting_time = sum(waiting_times) / len(waiting_times)
        sysreport.average_waiting_time = average_waiting_time

        """
        Turnaround Time = [finish - arrival]
        """
        turnaround_times = [job.finish_time - job.arrival_time for job in self.completed_jobs]
        sysreport.turnaround_times = turnaround_times

        average_turnaround_time = sum(turnaround_times) / len(turnaround_times)
        sysreport.average_turnaround_time = average_turnaround_time

        max_turnaround_time = max(turnaround_times)
        sysreport.max_turnaround_time = max_turnaround_time

        turnaround_times_sorted = sorted(turnaround_times)
        p95_index = int(0.95 * len(turnaround_times_sorted))
        p95_turnaround = turnaround_times_sorted[p95_index]
        sysreport.p95_turnaround = p95_turnaround

        """
        Service Time    = [finish - start]
        """
        service_times = [job.finish_time - job.start_time for job in self.completed_jobs]
        sysreport.service_times = service_times

        average_service_time = sum(service_times) / len(service_times)
        sysreport.average_service_time = average_service_time

        """
        Throughput      = [jobs completed / total time]
        """
        throughput = len(self.completed_jobs) / int(self.env.now)
        sysreport.throughput = throughput

        """
        Slowdown        = [turnaround / service]
                        = [finish - arrival / finish - start]
        """
        slowdowns = [
            (tt / st) if st > 0 else 0
            for tt, st in zip(turnaround_times, service_times)
        ]
        sysreport.slowdowns = slowdowns

        average_slowdown = sum(slowdowns) / len(slowdowns)
        sysreport.average_slowdown = average_slowdown

        p95_slowdown = sorted(slowdowns)[p95_index]
        sysreport.p95_slowdown = p95_slowdown

        # Return the report
        return sysreport


    def __str__(self):
        return "System Report:\n\t" + str(self.memory) + "\n\t" + str(self.generator) + "\n\t" + str(self.scheduler)