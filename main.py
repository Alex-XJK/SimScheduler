import simpy
import random
import logging
from System import System
from Memory import Memory
from Generator import Generator
from Schedulers.FCFS import FCFS
from Schedulers.RR import RR
from Schedulers.SRPT import SRPT


def main(sched_class="FCFS", batch_size=4):
    # 1. Create SimPy Environment
    env = simpy.Environment()
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    # 2. Define Memory Resource
    memory = Memory(env, capacity=300000, threshold=0.90)

    # 3. Define Scheduler
    if sched_class == "FCFS":
        scheduler = FCFS(env, memory=memory, batch=batch_size)
    elif sched_class == "RR":
        scheduler = RR(env, memory=memory, batch=batch_size, time_slice=100)
    elif sched_class == "SRPT":
        scheduler = SRPT(env, memory=memory, batch=batch_size)
    else:
        raise ValueError("Unknown scheduler type")

    # 4. Define Generator
    def random_init():
        return random.randint(1024, 2048)
    def random_output():
        return random.randint(1024, 8192)
    generator = Generator(env, scheduler=scheduler, speed=8, total=100, init_fn=random_init, output_fn=random_output)

    # 4. Create the System
    system = System(env, memory=memory, scheduler=scheduler, generator=generator)

    # 5. Run the simulation
    env.process(system.run_simulation(max_time=1000000))
    env.run()

    # 6. Print results
    print(system)
    system.report_stats()


if __name__ == "__main__":
    scheduler_type = "RR"  # "FCFS", "RR", "SRPT"

    main(scheduler_type, 1)