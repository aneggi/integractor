import multiprocessing
import time
import socket
import sys

import simulate_A
import simulate_B
import simulate_C
import simulate_D

def is_rabbitmq_running():
    try:
        with socket.create_connection(("localhost", 5672), timeout=5):
            return True
    except (socket.timeout, socket.error):
        return False

def supervisor():
    processes = {}
    workers = [
        simulate_A.main,
        simulate_B.main,
        simulate_C.main,
        simulate_D.main    
    ]

    for worker_id, target_function in enumerate(workers):
        process = multiprocessing.Process(target=target_function)
        process.start()
        processes[worker_id] = process
        print(f"Worker {worker_id} started.")

    while True:
        for worker_id, process in list(processes.items()):
            if not process.is_alive():
                target_function = workers[worker_id]
                print(f"Supervisor: Restarting worker {worker_id}...")
                processes[worker_id] = multiprocessing.Process(target=target_function)
                processes[worker_id].start()
        time.sleep(1)

if __name__ == "__main__":
    if not is_rabbitmq_running():
        print("RabbitMQ is not running on localhost. Please start RabbitMQ and try again.")
        sys.exit(1)
    supervisor()
