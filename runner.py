from main import main
def runner_main(batch_size=8):
    stats_list = []
    label_list = []

    # Simulation 1: SRPT
    print("Running SRPT simulation...")
    stats_srpt = main(sched_class="SRPT", batch_size=batch_size)
    stats_list.append(stats_srpt)
    label_list.append("SRPT")

    # Simulation 2: RR-1
    print("Running RR-1 simulation...")
    stats_rr1 = main(sched_class="RR", rr_time_slice=1, batch_size=batch_size)
    stats_list.append(stats_rr1)
    label_list.append("RR-1")

    # Simulation 3: RR-10
    print("Running RR-10 simulation...")
    stats_rr10 = main(sched_class="RR", rr_time_slice=10, batch_size=batch_size)
    stats_list.append(stats_rr10)
    label_list.append("RR-10")

    # Simulation 4: RR-100
    print("Running RR-100 simulation...")
    stats_rr100 = main(sched_class="RR", rr_time_slice=100, batch_size=batch_size)
    stats_list.append(stats_rr100)
    label_list.append("RR-100")

    # Simulation 5: FCFS
    print("Running FCFS simulation...")
    stats_fcfs = main(sched_class="FCFS", batch_size=batch_size)
    stats_list.append(stats_fcfs)
    label_list.append("FCFS")

if __name__ == "__main__":
    runner_main(batch_size=1)
