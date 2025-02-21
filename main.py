import simpy
import random
import logging
from System import System, SysReport
from Memory import Memory
from Generators.Random import RandomGenerator
from Generators.Loader import CSVSource, CSVGenerator
from Schedulers.FCFS import FCFS
from Schedulers.RR import RR
from Schedulers.SRPT import SRPT

import numpy as np


def zipf(s, min_tokens, max_tokens):
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



def main(sched_class="FCFS", rr_time_slice=10, batch_size=4, **kwargs) -> SysReport:
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
        scheduler = SRPT(env, memory=memory, batch=batch_size, **kwargs)
    else:
        raise ValueError("Unknown scheduler type")

    # 4. Define Generator
    # generator = RandomGenerator(
    #     env,
    #     scheduler=scheduler,
    #     speed=0.02,  # NOTE: this is double the achievable throughput
    #     total=1000,
    #     dropout=0.05,
    #     init_fn=lambda: random.randint(1024, 2048),
    #     output_fn=lambda: zipf(s=1.98, min_tokens=256, max_tokens=16384)
    # )
    generator = CSVGenerator(
        env,
        scheduler=scheduler,
        speed=0.02,  # NOTE: this is double the achievable throughput
        total=1000,
        dropout=0.05,
        csv_sources=[
            CSVSource(nickname="AzureChat", file_path="Generators/data/AzureLLMInferenceTrace_conv.csv", fraction=0.9),
            CSVSource(nickname="AzureCode", file_path="Generators/data/AzureLLMInferenceTrace_code.csv", fraction=0.1),
        ]
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

    res = main(sched_class=scheduler_type, rr_time_slice=1, batch_size=8)
    # Only print the string representation of the report --> No need, print will invoke my implemented __str__ method
    print(res)
