import logging
from dataclasses import dataclass

from Generators.BaseGenerator import Generator
from Device import Device
from Schedulers.GlobalScheduler import GlobalScheduler
from Job import Job
from Allocator import Allocator

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
    ttft_times: list[int] = None
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
    # TTFT metrics
    average_ttft: float = 0.0
    max_ttft: float = 0.0
    p95_ttft: float = 0.0
    p99_ttft: float = 0.0

    def __str__(self):
        return f"""
        -------------------- Simulation Results --------------------
        Total Time Elapsed: {self.total_time}
        Total Jobs Finished: {self.finished_jobs}
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
        Average TTFT: {self.average_ttft:.2f}
        Max TTFT: {self.max_ttft:.2f}
        95th Percentile TTFT: {self.p95_ttft:.2f}
        99th Percentile TTFT: {self.p99_ttft:.2f}
        -------------------- End of Report --------------------
        """

class System:
    """
    The main wrapper class for the system.
    """

    def __init__(self, env, generator: Generator, devices: list[Device], global_scheduler: GlobalScheduler):
        self.env = env

        self.generator: Generator = generator
        self.devices: list[Device] = devices
        self.global_scheduler: GlobalScheduler = global_scheduler
        self.allocator: Allocator = Allocator(self.global_scheduler, self.devices)

        # Bookkeeping for completed jobs
        self.completed_jobs: list[Job] = []


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

            # 4. Invoke Allocator to check if we need to online/offline devices
            self.allocator.step()

            # 5. Check if we are done on all devices and the generator
            if self.generator.is_finished and all(device.is_finished for device in self.devices):
                logging.info("All devices and generator are finished.")
                break

            # 6. Advance simulation time by 1 “second”
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
        Time-To-First-Token (TTFT) = [decode.start - arrival]
        """
        ttft_times = [job.decode_start_time - job.arrival_time for job in self.completed_jobs]
        sysreport.ttft_times = ttft_times

        sysreport.average_ttft = sum(ttft_times) / len(ttft_times)
        sysreport.max_ttft = max(ttft_times)

        ttft_times_sorted = sorted(ttft_times)
        p95_index = int(0.95 * len(ttft_times_sorted))
        p99_index = int(0.99 * len(ttft_times_sorted))
        sysreport.p95_ttft = ttft_times_sorted[p95_index]
        sysreport.p99_ttft = ttft_times_sorted[p99_index]

        # TODO: Definition of waiting time? [(prefill.start - arrival) + (decode.start - prefill.finish)]
        """
        Waiting Time    = [start - arrival]
        """
        waiting_times = [job.decode_start_time - job.arrival_time for job in self.completed_jobs]
        sysreport.waiting_times = waiting_times

        average_waiting_time = sum(waiting_times) / len(waiting_times)
        sysreport.average_waiting_time = average_waiting_time

        """
        Turnaround Time = [decode.finish - arrival]
        """
        turnaround_times = [job.decode_finish_time - job.arrival_time for job in self.completed_jobs]
        sysreport.turnaround_times = turnaround_times

        average_turnaround_time = sum(turnaround_times) / len(turnaround_times)
        sysreport.average_turnaround_time = average_turnaround_time

        max_turnaround_time = max(turnaround_times)
        sysreport.max_turnaround_time = max_turnaround_time

        turnaround_times_sorted = sorted(turnaround_times)
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

        # TODO: Definition of service time? [(decode.finish - decode.start) + (prefill.finish - prefill.start)]
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