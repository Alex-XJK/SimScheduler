import logging

from Device import Device
from Schedulers.GlobalScheduler import GlobalScheduler

class Allocator:
    """
    Dynamically manages a set of devices, bringing them online/offline based on workload.
    """

    def __init__(self, global_scheduler: GlobalScheduler, all_devices: list[Device], idle_threshold: int = 50):
        """
        :param global_scheduler: The GlobalScheduler instance.
        :param all_devices: A list of all possible devices (initially online or offline).
        :param idle_threshold: Number of consecutive idle steps after which to offline a device. -1 to disable.
        """
        self.global_scheduler: GlobalScheduler = global_scheduler
        self.online_devices: list[Device] = list(all_devices)
        self.offline_devices: list[Device] = []
        self.idle_threshold: int = idle_threshold

        # Track how many consecutive steps each device has been idle
        self.idle_counters = {device: 0 for device in all_devices}

        # Device types counting
        self.device_capable_counts = {mode: 0 for mode in Device.Mode}
        for device in self.online_devices:
            self.device_capable_counts[device.tag] += 1
        self.working_counters = {device: 0 for device in all_devices}


    def step(self) -> None:
        """
        Called once per simulation step to decide if we should offline or online devices.
        """
        # 1. Check usage of each online device
        for device in self.online_devices:
            # Register working counters
            self.working_counters[device] += 1

            # Skip workload check if device is warming up
            if device.is_warming_up:
                continue

            # Skip dynamic management if user set idle_threshold to -1
            if self.idle_threshold == -1:
                continue

            # Update idle counter
            if device.workload < 1e-6:
                self.idle_counters[device] += 1
            else:
                self.idle_counters[device] = 0

            # If idle for too long, offline it
            if self.idle_counters[device] >= self.idle_threshold:
                if self._okay_to_offline(device):
                    self.offline_device(device)

        # 2. If workload is high, bring some offline devices online
        if self.global_scheduler.all_devices_busy and self.offline_devices and self.idle_threshold >= 0:
            device_to_online = self.offline_devices[0]  # pick some device
            self.online_device(device_to_online)

    def offline_device(self, device) -> None:
        """
        Take 'device' offline. Remove it from the GlobalScheduler and from the online list.
        """
        if device in self.online_devices:
            logging.info(f"Allocator >> Prepare to offline device '{device.name}'")
            self.online_devices.remove(device)
            self.device_capable_counts[device.tag] -= 1
            self.idle_counters[device] = 0
            self.offline_devices.append(device)
            self.global_scheduler.remove_device(device)

    def online_device(self, device) -> None:
        """
        Bring 'device' back online, add it to the GlobalScheduler.
        """
        if device in self.offline_devices:
            logging.info(f"Allocator >> Prepare to online device '{device.name}'")
            self.offline_devices.remove(device)
            self.online_devices.append(device)
            self.device_capable_counts[device.tag] += 1
            self.idle_counters[device] = 0
            device.warm_up()
            self.global_scheduler.add_device(device)

    def _okay_to_offline(self, device: Device) -> bool:
        """
        Check if it's okay to offline the device.

        Policy:
        - We want to keep at least one device for Prefill, so that we can get ready for future user requests.
        - We should be able to offline all Decode devices if we have no Prefill jobs, and no running Decode jobs.
            - But this should also mean we finished the whole simulation :)

        :param device: The device to check.
        :return: True if it's okay to offline the device, False otherwise.
        """
        if device.tag == Device.Mode.PREFILL:
            return self.device_capable_counts[Device.Mode.PREFILL] + self.device_capable_counts[Device.Mode.MIXED] > 1
        elif device.tag == Device.Mode.DECODE:
            return self.device_capable_counts[Device.Mode.DECODE] + self.device_capable_counts[Device.Mode.MIXED] > 1
        elif device.tag == Device.Mode.MIXED:
            return (
                    self.device_capable_counts[Device.Mode.PREFILL] + self.device_capable_counts[Device.Mode.MIXED] > 1
                    and
                    self.device_capable_counts[Device.Mode.DECODE] + self.device_capable_counts[Device.Mode.MIXED] > 1
            )
        else:
            return False

    @property
    def all_devices(self) -> list[Device]:
        """
        Return all devices, online and offline.
        This is used to break the Python's shadow copy of the devices list.
        """
        return self.online_devices + self.offline_devices

    def __str__(self) -> str:
        total = 0
        s = "Allocator\n"
        for d, count in self.working_counters.items():
            s += f"\t{d.name}({d.tag}) :: online for {count} steps\n"
            total += count
        s += f"\tTotal Device Time: {total}\n"
        dyn_status = f"{self.idle_threshold} idle steps" if self.idle_threshold >= 0 else "Disabled"
        s += f"\tDynamic Management: {dyn_status}\n"
        return s
