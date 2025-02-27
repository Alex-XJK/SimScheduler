import logging

from Device import Device
from Job import Job

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

    def dispatch_job(self, job: Job) -> Device|None:
        """
        Select a device based on the current workload and dispatch the job to it.
        Returns the selected device.
        """
        capable_devices = self._get_capable_devices(job)
        sorted_devices = sorted(capable_devices, key=lambda d: d.workload)
        for sd in sorted_devices:
            if sd.add_job(job):
                logging.debug(f"GlobalScheduler: Dispatched job {job.job_id} to '{sd.name}'")
                return sd

        logging.warning(f"GlobalScheduler: No capable device found for job {job.job_id}")
        return None

    def _get_capable_devices(self, job: Job) -> list[Device]:
        """
        Return a list of devices that can support the job's state.
        """
        return [d for d in self.devices if d.job_state_supported(job)]