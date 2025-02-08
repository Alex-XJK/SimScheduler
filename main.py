import simpy
import random
import logging
from System import System
from Memory import Memory
from Generator import Generator
from Schedulers.FCFS import FCFS
from Schedulers.RR import RR
from Schedulers.SRPT import SRPT


def main(scheduler_type="FCFS"):
    # 1. Create SimPy Environment
    env = simpy.Environment()
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    # 2. Define Memory Resource
    memory = Memory(env, capacity=300000, threshold=0.95)

    # 3. Define Scheduler
    if scheduler_type == "FCFS":
        scheduler = FCFS(env, memory=memory)
    elif scheduler_type == "RR":
        scheduler = RR(env, memory=memory, batch=4, time_slice=10)
    elif scheduler_type == "SRPT":
        scheduler = SRPT(env, memory=memory)
    else:
        raise ValueError("Unknown scheduler type")

    # 4. Define Generator
    def random_M():
        return random.randint(1024, 8192)
    generator = Generator(env, scheduler=scheduler, speed=8, total=100, init_size=1024, final_fn=random_M)

    # 4. Create the System
    system = System(env, memory=memory, scheduler=scheduler, generator=generator)

    # 5. Run the simulation
    env.process(system.run_simulation(max_time=1000000))
    env.run()

    # 6. Print results
    print(system)
    print(scheduler.introduction())
    system.report_stats()


if __name__ == "__main__":
    scheduler_type = "RR"  # "FCFS", "RR", "SRPT"

    main(scheduler_type)