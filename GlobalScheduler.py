import logging

from Device import Device
from Job import Job


def print_devices(devices: list[Device]) -> str:
    msg = "Devices:\t"
    for d in devices:
        msg += f"{d.name}({d.tag}) {d.workload:.4f}\t"
    return msg


class GlobalScheduler:
    """
    Global scheduler that dispatches jobs to a pool of devices.
    """

    def __init__(self, devices: list[Device]):
        """
        Parameters:
          - devices: A list of Device instances.
        """
        self.devices = devices
        for d in self.devices:
            d.set_global_scheduler(self)
        self.queue: list[Job] = []
        self.statistics = dict.fromkeys(self.devices, 0)

    def _dispatch_job(self, job: Job) -> Device|None:
        """
        Select a device based on the current workload and dispatch the job to it.
        Returns the selected device.
        """
        capable_devices = self._get_capable_devices(job)
        sorted_devices = sorted(capable_devices, key=lambda d: d.workload)
        logging.debug(f"G-S >> Capable {print_devices(sorted_devices)}")
        for sd in sorted_devices:
            if sd.add_job(job):
                logging.debug(f"G-S >> Dispatched Job({job.job_id}) to '{sd.name}'")
                self.statistics[sd] += 1
                return sd

        logging.warning(f"G-S >> No capable device found for Job({job.job_id})")
        return None

    def receive_job(self, job: Job):
        """
        Receive a new job from the system.
        """
        self.queue.append(job)
        logging.debug(f"G-S >> Received Job({job.job_id}), queue length: {len(self.queue)}")
        return True

    def step(self):
        """
        Main step function called by the system.
        """
        for job in self.queue:
            if self._dispatch_job(job) is not None:
                self.queue.remove(job)

    def _get_capable_devices(self, job: Job) -> list[Device]:
        """
        Return a list of devices that can support the job's state.
        """
        return [d for d in self.devices if d.job_state_supported(job)]

    def __str__(self):
        s = "Global Scheduler\n"
        for d in self.devices:
            s += f"\t{d.name} ({d.tag}) :: dispatched {self.statistics[d]} jobs\n"
        return s