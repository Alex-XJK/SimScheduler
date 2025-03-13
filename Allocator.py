import logging


class Allocator:
    """
    Dynamically manages a set of devices, bringing them online/offline based on workload.
    """

    def __init__(self, global_scheduler, all_devices, idle_threshold=10):
        """
        :param global_scheduler: The GlobalScheduler instance.
        :param all_devices: A list of all possible devices (initially online or offline).
        :param idle_threshold: Number of consecutive idle steps after which to offline a device.
        """
        self.global_scheduler = global_scheduler
        self.online_devices = list(all_devices)
        self.offline_devices = []
        self.idle_threshold = idle_threshold

        # Track how many consecutive steps each device has been idle
        self.idle_counters = {device: 0 for device in all_devices}

    def step(self) -> None:
        """
        Called once per simulation step to decide if we should offline or online devices.
        """
    def offline_device(self, device) -> None:
        """
        Take 'device' offline. Remove it from the GlobalScheduler and from the online list.
        """
        if device in self.online_devices:
            self.online_devices.remove(device)
            self.offline_devices.append(device)
            logging.info(f"Allocator >> Offlined device {device.name}")

    def online_device(self, device) -> None:
        """
        Bring 'device' back online, add it to the GlobalScheduler.
        """
        if device in self.offline_devices:
            self.offline_devices.remove(device)
            self.online_devices.append(device)
            logging.info(f"Allocator >> Onlined device {device.name}")

    def __str__(self) -> str:
        return f"Allocator >> {len(self.online_devices)} online, {len(self.offline_devices)} offline."
