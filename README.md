# SimScheduler
Alex's Scheduler Experiment and Algorithm Simulator

## How to run

### Run the simulator with detailed information
#### Install dependencies
```bash
pip install simpy
```

#### Set configuration parameters
Set the scheduler type, batch size, etc. in the `main.py` file:
```python
scheduler_type = "RR"  # "FCFS", "RR", "SRPT"
```

#### Run the simulator
```bash
python main.py
```

### Run the simulator experiment and generate a report
#### Additional dependencies
```bash
pip install matplotlib numpy
```

#### Set batch size
In this comparison experiment, the batch size is the only parameter to set.
Edit the `batch_size` parameter in the `runner.py` file:
```python
runner_main(batch_size={Your Batch Size})
```

#### Run the simulator
```bash
python runner.py
```

#### Output
- Markdown Table format in the terminal
- PNG Graphs default to `./simulation_results.png`

## Explanation on statistics

- `Waiting Time` = `Start Time` - `Arrival Time`
- `Turnaround Time` = `Finish Time` - `Arrival Time`
- `Service Time` = `Finish Time` - `Start Time`
- `Throughput` = `Number of completed processes` / `Total time`
- `Slowdown` = `Turnaround Time` / `Service Time`

The calculations are done in the `report_stats` function of `System` class.

## Development

### Develop your own scheduler
1. Create a new file in the `~/Schedulers/` directory.
2. Inherit from the `Scheduler` class.
3. Implement the `pick_next_task` method to select and return the next Job to run.
4. Optionally, override other methods to customize behavior.
5. Add your scheduler to the `main.py` file.

See `~/Schedulers/FCFS.py` for a minimal example.

