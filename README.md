# SimScheduler
Alex's Scheduler Experiment and Algorithm Simulator

## Run the simulator and generate a report

### Install dependencies
```bash
pip install simpy matplotlib numpy
```

### Set batch size
In this comparison experiment, the batch size is the only parameter to set.
Edit the `batch_size` parameter in the `runner.py` file:
```python
runner_main(batch_size={Your Batch Size})
```

### Run the simulator
```bash
python3 runner.py
```

#### Output
- Markdown Table format in the terminal
- PNG Graphs default to `./simulation_results.png`

## Explanation on statistics

- `Waiting Time` = `Start Time` - `Arrival Time`
- `Turnaround Time` = `Finish Time` - `Arrival Time`
- `Service Time` = `Finish Time` - `Start Time`
- `Throughput` = `Number of completed processes` / `Total time`
- `Normalized Turnaround Time` = `Turnaround Time` / `Sequence Length`

The calculations are done in the `report_stats` function of `System` class.

## Development

### Debugging execution
For detailed logging messages and debugging, run the main file instead of the experiment runner.
You can edit each details of the configuration in the `main.py` file, and then run the following command:
```bash
python3 main.py
```

### Choose a Job Generator
Currently, the simulator supports two types of job generators:
- `RandomGenerator`: Generates random jobs with random arrival times and service times based on the user provided distribution function.
- `CSVGenerator`: Generates job parameters based on multiple CSV files. 
  - The CSV files should contain at least the following columns: `ContextTokens`, `GeneratedTokens` (e.g., the Azure dataset).


### Develop your own scheduler
1. Create a new file in the `~/Schedulers/` directory.
2. Inherit from the `Scheduler` class.
3. Implement the `pick_next_task` method to select and return the next Job to run.
4. Optionally, override other methods to customize behavior.
5. Add your scheduler to the `main.py` file.

See `~/Schedulers/FCFS.py` for a minimal example.

