import simpy
import random
import logging
from System import System
from Memory import Memory
from Generator import Generator
from Schedulers.FCFSScheduler import FCFSScheduler
from Schedulers.RRScheduler import RRScheduler
from Schedulers.RRRejectScheduler import RRRejectScheduler
from Schedulers.RRSwapScheduler import RRSwapScheduler
from Schedulers.RRWaitSwapScheduler import RRWaitSwapScheduler
from Schedulers.SRPTScheduler import SRPTScheduler

def main():
    # 1. Create SimPy Environment
    env = simpy.Environment()
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    # 2. Define Memory Resource
    memory = Memory(env, capacity=300000)

    # 3. Define Scheduler
    # scheduler = FCFSScheduler(env, memory=memory)
    # scheduler = RRScheduler(env, memory=memory, time_slice=1)
    # scheduler = RRRejectScheduler(env, memory=memory, time_slice=100, threshold=0.7)
    # scheduler = RRSwapScheduler(env, memory=memory, time_slice=100, threshold=0.9)
    scheduler = RRWaitSwapScheduler(env, memory=memory, time_slice=100, threshold=0.9)
    # scheduler = SRPTScheduler(env, memory=memory)

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
    system.report_stats()


if __name__ == "__main__":
    main()