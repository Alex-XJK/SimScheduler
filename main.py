import simpy
import random
import logging
from System import System
from Memory import Memory
from Generator import Generator
from RRScheduler import RRScheduler

def main():
    # 1. Create SimPy Environment
    env = simpy.Environment()
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    # 2. Define Memory Resource
    memory = Memory(env, capacity=200)

    # 3. Define Scheduler
    scheduler = RRScheduler(env, memory=memory, time_slice=1)

    # 4. Define Generator
    def random_M():
        return random.randint(10, 15)
    generator = Generator(env, scheduler=scheduler, speed=2, total=10, init_size=5, final_fn=random_M)

    # 4. Create the System
    system = System(env, memory=memory, scheduler=scheduler, generator=generator)
    print(system)

    # 5. Run the simulation
    env.process(system.run_simulation(max_time=100))
    env.run()

    # 6. Print results
    system.report_stats()


if __name__ == "__main__":
    main()