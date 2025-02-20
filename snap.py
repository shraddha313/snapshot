from threading import Thread, Lock
from queue import Queue


class Process(Thread):
    def __init__(self, pid, channels, balance, max_iterations):
        Thread.__init__(self)
        self.pid = pid
        self.channels = channels
        self.balance = balance
        self.local_snapshot = {}
        self.marker_sent = False
        self.marker_received = False
        self.lock = Lock()
        self.queue = Queue()
        self.max_iterations = max_iterations
        self.iteration = 0

    def send(self, amount, recipient):
        self.lock.acquire()
        self.balance -= amount
        self.channels[self.pid][recipient].put(amount)
        self.lock.release()

    def receive(self):
        messages = []
        while not self.queue.empty():
            message = self.queue.get()
            messages.append(message)
        return messages

    def run(self):
        while self.iteration < self.max_iterations:
            # Check if a marker has been received
            if self.marker_received:
                self.lock.acquire()
                self.marker_received = False
                self.local_snapshot[self.pid] = self.balance
                messages = self.receive()
                self.lock.release()

                # Send marker to all other processes
                for i in range(len(self.channels)):
                    if i != self.pid:
                        self.lock.acquire()
                        self.channels[self.pid][i].put("MARKER")
                        self.lock.release()

                # Send local snapshot and messages to other processes
                for i in range(len(self.channels)):
                    if i != self.pid:
                        self.lock.acquire()
                        self.channels[i][self.pid].put(
                            ("SNAPSHOT", self.pid, self.balance, messages)
                        )
                        self.lock.release()

            # Check if a marker needs to be sent
            if not self.marker_sent:
                # Perform some random transfers
                recipient = (self.pid + 1) % len(self.channels)
                amount = 10
                self.send(amount, recipient)

                # Send a marker to start the snapshot process
                self.lock.acquire()
                self.marker_sent = True
                self.channels[self.pid][recipient].put("MARKER")
                self.lock.release()

            # Check if a marker has been received after sending one
            if self.marker_received:
                self.lock.acquire()
                self.marker_received = False
                self.local_snapshot[self.pid] = self.balance
                self.marker_sent = False
                self.iteration += 1
                self.lock.release()


class Server:
    def __init__(self, processes):
        self.processes = processes
        self.global_snapshot = {}
        self.lock = Lock()

    def update_local_snapshot(self, sender, receiver, balance, messages):
        self.lock.acquire()
        if sender not in self.global_snapshot:
            self.global_snapshot[sender] = {}
        self.global_snapshot[sender][receiver] = {
            "balance": balance,
            "messages": messages,
        }
        self.lock.release()

    def get_global_snapshot(self):
        return self.global_snapshot


if __name__ == "__main__":
    # Create channels between processes
    channels = [[Queue() for _ in range(3)] for _ in range(3)]

    # Create three processes with their initial balances and maximum iterations
    # Create three processes with their initial balances and maximum iterations
    max_iterations = 10
    p0 = Process(0, channels, 100, max_iterations)
    p1 = Process(1, channels, 100, max_iterations)
    p2 = Process(2, channels, 100, max_iterations)

    # Create a server
    server = Server([p0, p1, p2])

    # Start the processes
    p0.start()
    p1.start()
    p2.start()

    # Wait for the processes to finish
    p0.join()
    p1.join()
    p2.join()

    # Get the global snapshot from the server
    global_snapshot = server.get_global_snapshot()
    print("Global Snapshot:")

    for sender, receivers in global_snapshot.items():
        for receiver, snapshot in receivers.items():
            print(f"Process {sender} -> Process {receiver}:")
            print(f"Balance: {snapshot['balance']}")
            print("Messages:")
            for message in snapshot["messages"]:
                print(message)
