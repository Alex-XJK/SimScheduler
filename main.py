import simpy
import random
from System import System
from RRScheduler import RRScheduler

def main():
    # 1. Create SimPy Environment
    env = simpy.Environment()

    # 2. Define scheduling policy (Round-Robin with timeslice=1)
    scheduler_cls = RRScheduler
    scheduler_kwargs = {'time_slice': 1}

    # 3. Define generator parameters
    S = 2  # generate 2 jobs per second
    X = 10  # total 10 jobs to generate
    L = 3  # average initial size (P)

    def random_M():
        return random.randint(5, 10)  # final size M is somewhere in 5..10

    generator_kwargs = {
        'S': S,
        'X': X,
        'L': L,
        'M_fn': random_M
    }

    # 4. Create the System
    system = System(env, memory_capacity=50,
                    scheduler_cls=scheduler_cls,
                    scheduler_kwargs=scheduler_kwargs,
                    generator_kwargs=generator_kwargs)

    # 5. Run the simulation
    system.run_simulation(max_time=50)  # run up to time=50

    # 6. Print results
    system.report_stats()


if __name__ == "__main__":
    main()