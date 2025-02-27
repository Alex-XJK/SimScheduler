import simpy
import logging
from System import System, SysReport
from Device import Device
from GlobalScheduler import GlobalScheduler
from Generators.Loader import CSVSource, CSVGenerator
from Schedulers.FCFS import FCFS
from Schedulers.RR import RR
from Schedulers.SRPT import SRPT



def main() -> SysReport:
    # 1. Create SimPy Environment
    env = simpy.Environment()

    # 2. Define Device(s)
    device1 = Device(env, memory_capacity=102400, scheduler_cls=FCFS, scheduler_kwargs={'batch': 2}, name="Device_1", tag=Device.Mode.MIXED)
    device2 = Device(env, memory_capacity=300000, scheduler_cls=RR, scheduler_kwargs={'batch': 8, 'time_slice': 10}, name="Device_2", tag=Device.Mode.MIXED)

    # 3. Define Global Scheduler
    global_sched = GlobalScheduler(devices=[device1, device2])

    # 4. Define Generator
    generator = CSVGenerator(
        env,
        scheduler=global_sched,
        speed=1,
        total=1000,
        dropout=0.05,
        csv_sources=[
            CSVSource(nickname="AzChat23", file_path="Generators/data/AzureLLMInferenceTrace_conv.csv", fraction=0.5),
            CSVSource(nickname="AzCode23", file_path="Generators/data/AzureLLMInferenceTrace_code.csv", fraction=0.5),
        ]
    )

    # 5. Create the System
    system = System(env, generator=generator, devices=[device1, device2], global_scheduler=global_sched)

    # 6. Run the simulation
    env.process(system.run_simulation(max_time=1000000))
    env.run()

    # 7. Print results
    print(system)
    return system.report_stats()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    res = main()
    print(res)
