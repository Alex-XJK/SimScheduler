import matplotlib.pyplot as plt
import numpy as np
import logging

from main import main
from System import SysReport

def plot_results(stats_list : list[SysReport], label_list : list[str], save_path="simulation_results.png"):
    """
    Plot the CDFs for Turnaround Time and Slowdown for multiple simulation results,
    and save the resulting figure to the specified location.

    Parameters:
        stats_list: list of SysReport

        label_list: list of str
            Labels corresponding to each result.

        save_path: str
            The file path (including filename and extension) to save the generated image.
    """
    # Create a figure with two subplots: one for Turnaround Time and one for Slowdown
    fig, axs = plt.subplots(1, 2, figsize=(14, 6))

    # Plot Turnaround Time CDF on the first subplot
    for stats, label in zip(stats_list, label_list):
        # Convert turnaround_times to numpy array and ensure it's not None
        if hasattr(stats, 'turnaround_times') and stats.turnaround_times:
            data = np.asarray(stats.turnaround_times, dtype=float)
            if data.size > 0:  # Check if array is not empty
                sorted_data = np.sort(data)
                cdf = np.linspace(0, 100, len(sorted_data))
                axs[0].plot(cdf, sorted_data, label=label)
    axs[0].set_ylabel("Turnaround Time")
    axs[0].set_xlabel("Percentile (%)")
    axs[0].set_title("Turnaround Time")
    axs[0].legend()
    axs[0].grid(True)

    # Plot Slowdown CDF on the second subplot
    for stats, label in zip(stats_list, label_list):
        # Convert slowdowns to numpy array and ensure it's not None
        if hasattr(stats, 'normalized_turnaround_times') and stats.normalized_turnaround_times:
            data = np.asarray(stats.normalized_turnaround_times, dtype=float)
            if data.size > 0:  # Check if array is not empty
                sorted_data = np.sort(data)
                cdf = np.linspace(0, 100, len(sorted_data))
                axs[1].plot(cdf, sorted_data, label=label)
    axs[1].set_ylabel("Slowdown")
    axs[1].set_xlabel("Percentile (%)")
    axs[1].set_title("Slowdown")
    axs[1].legend()
    axs[1].grid(True)

    plt.tight_layout()
    # Save the figure to the provided file path
    plt.savefig(save_path)
    plt.close(fig)
    print(f"Plot saved to {save_path}")

def generate_markdown_table(stats_list : list[SysReport], label_list : list[str]):
    """
    Generate a markdown table comparing the average turnaround time and slowdown for each simulation result.

    Parameters:
        stats_list: list of SysReport

        label_list: list of str
            Labels corresponding to each result.
    """
    # Table header
    print("| Metric | " + " | ".join(label_list) + " |")
    print("|--------|" + "|".join(["---"] * len(label_list)) + "|")

    # Table Row: Total Time
    total_times = [stats.total_time for stats in stats_list]
    print("| Total Time | " + " | ".join([f"{time}" for time in total_times]) + " |")

    # Table Row: Throughput
    throughputs = [stats.throughput for stats in stats_list]
    print("| Throughput | " + " | ".join([f"{tp:.10f}" for tp in throughputs]) + " |")

    # Table Row: Average Waiting Time
    avg_waiting_times = [stats.average_waiting_time for stats in stats_list]
    print("| Average Waiting Time | " + " | ".join([f"{wt:.2f}" for wt in avg_waiting_times]) + " |")

    # Table Row: Average Turnaround Time
    avg_turnaround_times = [stats.average_turnaround_time for stats in stats_list]
    print("| Average Turnaround Time | " + " | ".join([f"{tt:.2f}" for tt in avg_turnaround_times]) + " |")

    # Table Row: 95th Percentile Turnaround Time
    p95_turnaround_times = [stats.p95_turnaround for stats in stats_list]
    print("| 95th Percentile Turnaround Time | " + " | ".join([f"{ptt:.2f}" for ptt in p95_turnaround_times]) + " |")

    # Table Row: 99th Percentile Turnaround Time
    p99_turnaround_times = [stats.p99_turnaround for stats in stats_list]
    print("| 99th Percentile Turnaround Time | " + " | ".join([f"{ptt:.2f}" for ptt in p99_turnaround_times]) + " |")

    # Table Row: Max Turnaround Time
    max_turnaround_times = [stats.max_turnaround_time for stats in stats_list]
    print("| Max Turnaround Time | " + " | ".join([f"{mtt:.2f}" for mtt in max_turnaround_times]) + " |")

    # Table Row: Average Slowdown
    avg_slowdowns = [stats.average_normalized_turnaround for stats in stats_list]
    print("| Average Slowdown | " + " | ".join([f"{sd:.6f}" for sd in avg_slowdowns]) + " |")

    # Table Row: 95th Percentile Slowdown
    p95_slowdowns = [stats.p95_normalized_turnaround for stats in stats_list]
    print("| 95th Percentile Slowdown | " + " | ".join([f"{sd:.6f}" for sd in p95_slowdowns]) + " |")

    # Table Row: 99th Percentile Slowdown
    p99_slowdowns = [stats.p99_normalized_turnaround for stats in stats_list]
    print("| 99th Percentile Slowdown | " + " | ".join([f"{sd:.6f}" for sd in p99_slowdowns]) + " |")


def runner_main(batch_size=8):
    stats_list : list[SysReport] = []
    label_list : list[str] = []

    # Simulation 1: SRPT
    print("Running SRPT (no starvation prevention) simulation...")
    stats_srpt = main(sched_class="SRPT", batch_size=batch_size, priority_quantum=None, starvation_threshold=None)
    stats_list.append(stats_srpt)
    label_list.append("SRPT")
    print(stats_srpt)

    print("Running SRPT (PQ 1, ST 50) simulation...")
    stats_srpt = main(sched_class="SRPT", batch_size=batch_size, priority_quantum=1, starvation_threshold=50)
    stats_list.append(stats_srpt)
    label_list.append("SRPT-1-50")
    print(stats_srpt)

    print("Running SRPT (PQ 5, ST 50) simulation...")
    stats_srpt = main(sched_class="SRPT", batch_size=batch_size, priority_quantum=5, starvation_threshold=50)
    stats_list.append(stats_srpt)
    label_list.append("SRPT-5-50")
    print(stats_srpt)
    
    print("Running SRPT (PQ 25, ST 50) simulation...")
    stats_srpt = main(sched_class="SRPT", batch_size=batch_size, priority_quantum=10, starvation_threshold=50)
    stats_list.append(stats_srpt)
    label_list.append("SRPT-25-50")
    print(stats_srpt)

    print("Running SRPT (PQ 1, ST 100) simulation...")
    stats_srpt = main(sched_class="SRPT", batch_size=batch_size, priority_quantum=1, starvation_threshold=100)
    stats_list.append(stats_srpt)
    label_list.append("SRPT-1-100")
    print(stats_srpt)

    print("Running SRPT (PQ 10, ST 100) simulation...")
    stats_srpt = main(sched_class="SRPT", batch_size=batch_size, priority_quantum=10, starvation_threshold=100)
    stats_list.append(stats_srpt)
    label_list.append("SRPT-10-100")
    print(stats_srpt)

    print("Running SRPT (PQ 50, ST 100) simulation...")
    stats_srpt = main(sched_class="SRPT", batch_size=batch_size, priority_quantum=50, starvation_threshold=100)
    stats_list.append(stats_srpt)
    label_list.append("SRPT-50-100")
    print(stats_srpt)

    print("Running SRPT (PQ 1, ST 1000) simulation...")
    stats_srpt = main(sched_class="SRPT", batch_size=batch_size, priority_quantum=1, starvation_threshold=1000)
    stats_list.append(stats_srpt)
    label_list.append("SRPT-1-1000")
    print(stats_srpt)

    print("Running SRPT (PQ 100, ST 1000) simulation...")
    stats_srpt = main(sched_class="SRPT", batch_size=batch_size, priority_quantum=100, starvation_threshold=1000)
    stats_list.append(stats_srpt)
    label_list.append("SRPT-100-1000")
    print(stats_srpt)

    print("Running SRPT (PQ 500, ST 1000) simulation...")
    stats_srpt = main(sched_class="SRPT", batch_size=batch_size, priority_quantum=500, starvation_threshold=1000)
    stats_list.append(stats_srpt)
    label_list.append("SRPT-500-1000")
    print(stats_srpt)

    # Simulation 2: RR-1
    print("Running RR-1 simulation...")
    stats_rr1 = main(sched_class="RR", rr_time_slice=1, batch_size=batch_size)
    stats_list.append(stats_rr1)
    label_list.append("RR-1")
    print(stats_rr1)

    # Simulation 3: RR-10
    print("Running RR-10 simulation...")
    stats_rr10 = main(sched_class="RR", rr_time_slice=10, batch_size=batch_size)
    stats_list.append(stats_rr10)
    label_list.append("RR-10")
    print(stats_rr10)

    # Simulation 4: RR-100
    print("Running RR-100 simulation...")
    stats_rr100 = main(sched_class="RR", rr_time_slice=100, batch_size=batch_size)
    stats_list.append(stats_rr100)
    label_list.append("RR-100")
    print(stats_rr100)

    # Simulation 5: FCFS
    print("Running FCFS simulation...")
    stats_fcfs = main(sched_class="FCFS", batch_size=batch_size)
    stats_list.append(stats_fcfs)
    label_list.append("FCFS")
    print(stats_fcfs)

    generate_markdown_table(stats_list, label_list)

    plot_results(stats_list, label_list, save_path="simulation_results.png")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN, format='%(levelname)s : %(message)s')

    runner_main(batch_size=16)
