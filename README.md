# SimScheduler
Alex's Scheduler Experiment and Algorithm Simulator

## How to run

### Install dependencies
```bash
pip install simpy
```

### Select a scheduler
Set the scheduler type in the `main.py` file:
```python
scheduler_type = "RR"  # "FCFS", "RR", "SRPT"
```

### Run the simulator
```bash
python main.py
```

## Explanation on statistics
- `Waiting Time = Start Time - Arrival Time`
- `Turnaround Time = Finish Time - Arrival Time`
- `Service Time = Finish Time - Start Time`
- `Throughput = Number of completed processes / Total time`
- `Slowdown = Turnaround Time / Service Time`

The calculations are done in the `report_stats` function of `System` class.

## Development

### Develop your own scheduler
1. Create a new file in the `~/Schedulers/` directory.
2. Inherit from the `Scheduler` class.
3. Implement the `pick_next_task` method to select and return the next Job to run.
4. Implement the `introduction` method to return a string describing your scheduler.
5. Optionally, override other methods to customize behavior.
6. Add your scheduler to the `main.py` file.

See `~/Schedulers/FCFS.py` for a minimal example.

