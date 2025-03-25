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

    def __init__(self, devices: list[Device], perform_load_balance=False):
        """
        Parameters:
          - devices: A list of Device instances.
        """
        self.perform_load_balance = perform_load_balance
        self.devices = devices
        for d in self.devices:
            d.set_global_scheduler(self)
        self.queue: list[Job] = []
        self.statistics = dict.fromkeys(self.devices, 0)

    def add_device(self, device: Device):
        """
        Add a device to the global scheduler.
        """
        self.devices.append(device)
        device.set_global_scheduler(self)
        if device not in self.statistics:
            self.statistics[device] = 0
        logging.info(f"G-S >> Added device '{device.name}'")

    def remove_device(self, device: Device):
        """
        Remove a device from the global scheduler.
        """
        if device in self.devices:
            self.devices.remove(device)
            logging.info(f"G-S >> Removed device '{device.name}'")

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

    def proactively_load_balance(self) -> int:
        """
        Proactively load balance the devices.
        Check and move preempt-able jobs from the heavily loaded devices to the lightly loaded devices.
        :return: The number of jobs moved.
        TODO: How many jobs to move?
        """
        moved_jobs = 0
        # Check Prefill stage jobs from Prefill-only or Mixed Devices
        prefill_devices = [d for d in self.devices if (d.tag == Device.Mode.PREFILL or d.tag == Device.Mode.MIXED)]
        sorted_pd = sorted(prefill_devices, key=lambda d: d.workload, reverse=True)
        lightest_prefill = sorted_pd[-1]
        for heavier_prefill in sorted_pd:
            if heavier_prefill.workload > 1.2 * lightest_prefill.workload:
                victim_job = heavier_prefill.scheduler.pick_movable_job([Job.State.INITIAL, Job.State.PREFILL])
                if (
                        victim_job is not None and
                        heavier_prefill.scheduler.preempt_job(victim_job) and
                        lightest_prefill.add_job(victim_job)
                ):
                    moved_jobs += 1
                    logging.debug(f"G-S >> Moving Job({victim_job.job_id}) from '{heavier_prefill.name}' to '{lightest_prefill.name}'")
                    break

        # Check Decode stage jobs from Decode-only or Mixed Devices
        decode_devices = [d for d in self.devices if (d.tag == Device.Mode.DECODE or d.tag == Device.Mode.MIXED)]
        sorted_dd = sorted(decode_devices, key=lambda d: d.workload, reverse=True)
        lightest_decode = sorted_dd[-1]
        for heavier_decode in sorted_dd:
            if heavier_decode.workload > 1.2 * lightest_decode.workload:
                victim_job = heavier_decode.scheduler.pick_movable_job([Job.State.DECODE])
                if (
                        victim_job is not None and
                        heavier_decode.scheduler.preempt_job(victim_job) and
                        lightest_decode.add_job(victim_job)
                ):
                    moved_jobs += 1
                    logging.debug(f"G-S >> Moving Job({victim_job.job_id}) from '{heavier_decode.name}' to '{lightest_decode.name}'")
        return moved_jobs

    def step(self):
        """
        Main step function called by the system.
        """
        # Proactively load balance the devices
        if self.perform_load_balance:
            self.proactively_load_balance()
        # Dispatch jobs in the queue
        for job in self.queue:
            if self._dispatch_job(job) is not None:
                self.queue.remove(job)

    @property
    def all_devices_busy(self) -> bool:
        """
        Check if all devices are busy.

        Notice:
        - 1.5 is the threshold for busy devices for now. 1.5 = (0.02 * 50 Jobs) + (1.0 * Half Memory Used)
        """
        return all(d.workload > 1.5 for d in self.devices)

    def _get_capable_devices(self, job: Job) -> list[Device]:
        """
        Return a list of devices that can support the job's state.
        """
        return [d for d in self.devices if d.job_state_supported(job)]

    def __str__(self):
        s = "Global Scheduler\n"
        for d, count in self.statistics.items():
            s += f"\t{d.name}({d.tag}) :: dispatched {count} jobs\n"
        return s