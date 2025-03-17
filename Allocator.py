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
        :param idle_threshold: Number of consecutive idle steps after which to offline a device.
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

    def step(self) -> None:
        """
        Called once per simulation step to decide if we should offline or online devices.
        """
        # 1. Check usage of each online device
        for device in self.online_devices:
            if device.workload < 1e-6:
                self.idle_counters[device] += 1
            else:
                self.idle_counters[device] = 0

            # If idle for too long, offline it
            if self.idle_counters[device] >= self.idle_threshold:
                if self._okay_to_offline(device):
                    self.offline_device(device)

        # 2. If workload is high, bring some offline devices online
        if self.global_scheduler.all_devices_busy and self.offline_devices:
            device_to_online = self.offline_devices[0]  # pick some device
            self.online_device(device_to_online)

    def offline_device(self, device) -> None:
        """
        Take 'device' offline. Remove it from the GlobalScheduler and from the online list.
        """
        if device in self.online_devices:
            self.online_devices.remove(device)
            self.device_capable_counts[device.tag] -= 1
            self.offline_devices.append(device)
            self.global_scheduler.remove_device(device)
            logging.info(f"Allocator >> Offline device {device.name}")

    def online_device(self, device) -> None:
        """
        Bring 'device' back online, add it to the GlobalScheduler.
        """
        if device in self.offline_devices:
            self.offline_devices.remove(device)
            self.online_devices.append(device)
            self.device_capable_counts[device.tag] += 1
            self.global_scheduler.add_device(device)
            logging.info(f"Allocator >> Online device {device.name}")

    def _okay_to_offline(self, device: Device) -> bool:
        """
        Check if it's okay to offline the device.

        Policy:
        - We want to keep at least one device for Prefill and Decode

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

    def __str__(self) -> str:
        return f"Allocator >> {len(self.online_devices)} online, {len(self.offline_devices)} offline."
