import simpy
import random
import logging
from System import System, SysReport
from Memory import Memory
from Generator import Generator
from Schedulers.FCFS import FCFS
from Schedulers.RR import RR
from Schedulers.SRPT import SRPT


def main(sched_class="FCFS", rr_time_slice=10, batch_size=4) -> SysReport:
    # 1. Create SimPy Environment
    env = simpy.Environment()

    # 2. Define Memory Resource
    memory = Memory(env, capacity=300000, threshold=0.90)

    # 3. Define Scheduler
    if sched_class == "FCFS":
        scheduler = FCFS(env, memory=memory, batch=batch_size)
    elif sched_class == "RR":
        scheduler = RR(env, memory=memory, batch=batch_size, time_slice=rr_time_slice)
    elif sched_class == "SRPT":
        scheduler = SRPT(env, memory=memory, batch=batch_size)
    else:
        raise ValueError("Unknown scheduler type")

    # 4. Define Generator
    generator = Generator(
        env,
        scheduler=scheduler,
        speed=8,
        total=100,
        init_fn=lambda: random.randint(1024, 2048),
        output_fn=lambda: random.randint(256, 16384),
        dropout=0.6
    )

    # 4. Create the System
    system = System(env, memory=memory, scheduler=scheduler, generator=generator)

    # 5. Run the simulation
    env.process(system.run_simulation(max_time=1000000))
    env.run()

    # 6. Print results
    print(system)
    return system.report_stats()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    scheduler_type = "RR"  # "FCFS", "RR", "SRPT"

    main(sched_class=scheduler_type, rr_time_slice=1, batch_size=8)