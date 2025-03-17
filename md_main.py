import simpy
import logging
from System import System, SysReport
from Device import Device
from Schedulers.GlobalScheduler import GlobalScheduler
from Generators.Loader import CSVSource, CSVGenerator
from Schedulers.FCFS import FCFS
from Schedulers.RR import RR
from Schedulers.FCFS_prefill import FCFSPre
from Schedulers.Hybrid_FR import HybridFR


def main() -> SysReport:
    # 1. Create SimPy Environment
    env = simpy.Environment()

    # 2. Define Device(s)
    # Our Standard Prefill device
    dev_p1 = Device(env,
                    name="Prefill_1", tag=Device.Mode.PREFILL,
                    memory_capacity=100000, memory_kwargs={'threshold': 0.95},
                    scheduler_cls=FCFSPre, scheduler_kwargs={'chunk_size': 512, 'chunk_time': 5})
    # Our new fancy decode device
    dev_d1 = Device(env,
                    name="Decode_1", tag=Device.Mode.DECODE,
                    memory_capacity=200000, memory_kwargs={'threshold': 0.95},
                    scheduler_cls=RR, scheduler_kwargs={'batch': 16, 'time_slice': 10})
    # Our old fashioned decode device
    dev_d2 = Device(env,
                    name="Decode_2", tag=Device.Mode.DECODE,
                    memory_capacity=50000, memory_kwargs={'threshold': 0.99},
                    scheduler_cls=FCFS, scheduler_kwargs={'batch': 2})
    # Our Hybrid device with balanced performance
    dev_m1 = Device(env,
                    name="Mixed_1", tag=Device.Mode.MIXED,
                    memory_capacity=150000, memory_kwargs={'threshold': 0.95},
                    scheduler_cls=HybridFR, scheduler_kwargs={'chunk_size': 128, 'chunk_time': 5, 'collocate_threshold': 1, 'time_slice': 1})
    dev_list = [dev_p1, dev_d1, dev_d2, dev_m1]

    # 3. Define Global Scheduler
    global_sched = GlobalScheduler(devices=dev_list)

    # 4. Define Generator
    generator = CSVGenerator(
        env,
        scheduler=global_sched,
        speed=2,
        total=1000,
        dropout=0.05,
        csv_sources=[
            CSVSource(nickname="AzChat23", file_path="Generators/data/AzureLLMInferenceTrace_conv.csv", fraction=0.5),
            CSVSource(nickname="AzCode23", file_path="Generators/data/AzureLLMInferenceTrace_code.csv", fraction=0.5),
        ]
    )

    # 5. Create the System
    system = System(env, generator=generator, devices=dev_list, global_scheduler=global_sched)

    # 6. Run the simulation
    env.process(system.run_simulation(max_time=1000000))
    env.run()

    # 7. Print results
    print(system.allocator)
    print(system.global_scheduler)
    print(system.generator)
    return system.report_stats()


if __name__ == "__main__":
    """
    Main entry point for multi-device simulation.
    """
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    res = main()
    print(res)
