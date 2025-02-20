import threading
import time

class Process:

    def __init__(self, id, balance, processes):
        self.id = id
        self.balance = balance
        self.processes = processes
        self.channel_state = {}
        self.recording = False

    def send_money(self, receiver, amount):
        receiver.receive_money(self, amount)
        self.balance -= amount
        if self.recording:
            self.channel_state[receiver] += amount

    def receive_money(self, sender, amount):
        if not self.recording:
            self.initiate_snapshot()
        self.balance += amount
        if self.recording:
            self.channel_state[sender] -= amount

    def initiate_snapshot(self):
        print(f"Initiating snapshot for process {self.id}")
        self.recording = True
        self.state = self.balance
        for process in self.processes:
            if process != self:
                self.channel_state[process] = 0

    def print_state(self):
        print(f"Process {self.id}: State {self.state}, Channel State {self.channel_state}")

def main():
    # Create processes
    p1 = Process(1, 500, [])
    p2 = Process(2, 500, [])
    p3 = Process(3, 500, [])
    
    # Establish connections
    p1.processes = [p2, p3]
    p2.processes = [p1, p3]
    p3.processes = [p1, p2]

    # Start transactions
    transaction_thread_1 = threading.Thread(target=p1.initiate_transactions)
    transaction_thread_2 = threading.Thread(target=p2.initiate_transactions)
    transaction_thread_3 = threading.Thread(target=p3.initiate_transactions)

    transaction_thread_1.start()
    transaction_thread_2.start()
    transaction_thread_3.start()

    transaction_thread_1.join()
    transaction_thread_2.join()
    transaction_thread_3.join()

    # Print final state
    p1.print_state()
    p2.print_state()
    p3.print_state()

if __name__ == "__main__":
    main()
