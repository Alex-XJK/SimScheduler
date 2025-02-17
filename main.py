import simpy
import random
import logging
from System import System, SysReport
from Memory import Memory
from Generator import Generator
from Schedulers.FCFS import FCFS
from Schedulers.RR import RR
from Schedulers.SRPT import SRPT

import numpy as np


def zipf(s=1.98, min_tokens=256, max_tokens=16384):
    """
    Generate a request length between min_tokens and max_tokens using a truncated
    Zipf distribution with exponent s.
    
    Approximately 95% of the probability mass will produce lengths below 4096 tokens.
    """
    # Create an array of possible token counts.
    ks = np.arange(min_tokens, max_tokens + 1)
    
    # Compute the unnormalized weights following Zipf's law: P(k) ∝ k^{-s}
    weights = ks ** (-s)
    
    # Compute the cumulative distribution function (CDF)
    cdf = np.cumsum(weights)
    cdf /= cdf[-1]  # normalize to 1
    
    # Draw a random number and use inverse transform sampling.
    u = np.random.rand()
    idx = np.searchsorted(cdf, u)
    return int(ks[idx])



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
        speed=0.012,  # NOTE: this is double the achievable throughput
        total=1000,
        init_fn=lambda: random.randint(1024, 2048),
        output_fn=lambda: zipf(),
        dropout=0.05
    )

    # 4. Create the System
    system = System(env, memory=memory, scheduler=scheduler, generator=generator)

    # 5. Run the simulation
    env.process(system.run_simulation(max_time=1000000))
    env.run()

    # 6. Print results
    print(str(system))
    return system.report_stats()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    scheduler_type = "RR"  # "FCFS", "RR", "SRPT"

    res = main(sched_class=scheduler_type, rr_time_slice=1, batch_size=8)
    # Only print the string representation of the report
    print(str(res))
