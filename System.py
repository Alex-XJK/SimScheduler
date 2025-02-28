import simpy
import logging
from dataclasses import dataclass

from Generator import Generator
from Device import Device
from GlobalScheduler import GlobalScheduler
from Job import Job


@dataclass
class SysReport:
    """
    Class for holding and transferring system statistics.
    """
    # Job statistics
    total_time: int = 0
    finished_jobs: int = 0
    throughput: float = 0.0
    # Raw arrays
    waiting_times: list[int] = None
    turnaround_times: list[int] = None
    service_times: list[int] = None
    normalized_turnaround_times: list[float] = None
    # Computed statistics
    average_waiting_time: float = 0.0
    average_turnaround_time: float = 0.0
    max_turnaround_time: float = 0.0
    p95_turnaround: float = 0.0
    p99_turnaround: float = 0.0
    average_service_time: float = 0.0
    p95_service: float = 0.0
    p99_service: float = 0.0
    # Add new normalized turnaround time metrics
    average_normalized_turnaround: float = 0.0
    max_normalized_turnaround: float = 0.0
    p95_normalized_turnaround: float = 0.0
    p99_normalized_turnaround: float = 0.0

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
        99th Percentile Turnaround Time: {self.p99_turnaround:.2f}
        Average Service Time: {self.average_service_time:.2f}
        95th Percentile Service Time: {self.p95_service:.2f}
        99th Percentile Service Time: {self.p99_service:.2f}
        Average Slowdown: {self.average_normalized_turnaround:.2f}
        95th Percentile Slowdown: {self.p95_normalized_turnaround:.2f}
        99th Percentile Slowdown: {self.p99_normalized_turnaround:.2f}
        -------------------- End of Report --------------------
        """

class System:
    """
    The main wrapper class for the system.
    """

    def __init__(self, env, generator : Generator, devices: list[Device], global_scheduler: GlobalScheduler):
        self.env = env

        self.generator = generator
        self.devices = devices
        self.global_scheduler = global_scheduler

        # Bookkeeping for completed jobs
        self.completed_jobs = []


    def run_simulation(self, max_time=1000):
        while self.env.now < max_time:
            # 0. Print current time
            logging.debug(f"---------- Time: {self.env.now} ----------")

            # 1. Generate new jobs for this step
            self.generator.generate_jobs()

            # 2. Dispatch jobs to devices
            self.global_scheduler.step()

            # 3. Instruct every device to work on their jobs
            for device in self.devices:
                selected_jobs = device.step()
                s = f"{device.name} :: ["
                for job in selected_jobs:
                    if job.state == Job.State.PREFILL:
                        s += f"{job.job_id}(P), "
                    elif job.state == Job.State.DECODE:
                        s += f"{job.job_id}(D), "
                    else:
                        s += f"{job.job_id}(?), "
                s += f"]"
                logging.debug(s)

            # 4. Check if we are done on all devices and the generator
            if self.generator.is_finished and all(device.is_finished for device in self.devices):
                logging.info("All devices and generator are finished.")
                break

            # 5. Advance simulation time by 1 “second”
            yield self.env.timeout(1)

        # End while
        logging.info(f"Simulation ended at time {self.env.now}")
        self.completed_jobs = [job for device in self.devices for job in device.scheduler.get_finished_jobs()]


    def report_stats(self) -> SysReport:
        sysreport = SysReport()

        sysreport.total_time = self.env.now
        sysreport.finished_jobs = len(self.completed_jobs)

        if len(self.completed_jobs) == 0:
            return sysreport

        """
        Waiting Time    = [start - arrival]
        """
        waiting_times = [job.decode_start_time - job.arrival_time for job in self.completed_jobs]
        sysreport.waiting_times = waiting_times

        average_waiting_time = sum(waiting_times) / len(waiting_times)
        sysreport.average_waiting_time = average_waiting_time

        """
        Turnaround Time = [finish - arrival]
        """
        turnaround_times = [job.decode_finish_time - job.arrival_time for job in self.completed_jobs]
        sysreport.turnaround_times = turnaround_times

        average_turnaround_time = sum(turnaround_times) / len(turnaround_times)
        sysreport.average_turnaround_time = average_turnaround_time

        max_turnaround_time = max(turnaround_times)
        sysreport.max_turnaround_time = max_turnaround_time

        turnaround_times_sorted = sorted(turnaround_times)
        p95_index = int(0.95 * len(turnaround_times_sorted))
        p99_index = int(0.99 * len(turnaround_times_sorted))
        p95_turnaround = turnaround_times_sorted[p95_index]
        p99_turnaround = turnaround_times_sorted[p99_index]
        sysreport.p95_turnaround = p95_turnaround
        sysreport.p99_turnaround = p99_turnaround

        """
        Normalized Turnaround Time = [turnaround_time / sequence_length]
        """
        normalized_turnaround_times = [
            tt / (job.final_size - job.init_size) for tt, job in zip(turnaround_times, self.completed_jobs)
        ]
        
        sysreport.normalized_turnaround_times = normalized_turnaround_times
        sysreport.average_normalized_turnaround = sum(normalized_turnaround_times) / len(normalized_turnaround_times)
        sysreport.max_normalized_turnaround = max(normalized_turnaround_times)
        
        normalized_turnaround_sorted = sorted(normalized_turnaround_times)
        sysreport.p95_normalized_turnaround = normalized_turnaround_sorted[p95_index]
        sysreport.p99_normalized_turnaround = normalized_turnaround_sorted[p99_index]

        """
        Service Time    = [finish - start]
        """
        service_times = [job.decode_finish_time - job.decode_start_time for job in self.completed_jobs]
        sysreport.service_times = service_times

        average_service_time = sum(service_times) / len(service_times)
        sysreport.average_service_time = average_service_time

        service_times_sorted = sorted(service_times)
        sysreport.p95_service = service_times_sorted[p95_index]
        sysreport.p99_service = service_times_sorted[p99_index]

        """
        Throughput      = [jobs completed / total time]
        """
        throughput = len(self.completed_jobs) / int(self.env.now)
        sysreport.throughput = throughput

        # Return the report
        return sysreport


    def __str__(self):
        s = f"System Report\n"
        s += f"\t{self.generator}\n"
        for device in self.devices:
            s += f"\t{device}\n"
        return s