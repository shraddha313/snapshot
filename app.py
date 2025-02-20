class Process:
    def __init__(self, id, balance):
        self.id = id
        self.balance = balance
        self.state = None
        self.channel_state = {}
        self.neighbors = []

    def send_money(self, receiver, amount):
        self.balance -= amount
        receiver.receive_money(self, amount)

    def receive_money(self, sender, amount):
        self.balance += amount

        if self.state is not None:
            if sender not in self.channel_state:
                self.channel_state[sender] = 0
            self.channel_state[sender] += amount

    def record_state(self):
        if self.state is None:
            self.state = self.balance
            for neighbor in self.neighbors:
                neighbor.record_state()

    def is_recording_complete(self):
        return len(self.channel_state) == len(self.neighbors)

    def __str__(self):
        return f"Process {self.id}: State {self.state}, Channel State {self.channel_state}"


class Network:
    def __init__(self, processes):
        self.processes = processes

    def initiate_snapshot(self, initiator_id):
        initiator = self.processes[initiator_id]
        initiator.record_state()

    def __str__(self):
        return "\n".join(str(process) for process in self.processes)


if __name__ == "__main__":
    # Initialize processes
    p1 = Process(1, 500)
    p2 = Process(2, 500)
    p3 = Process(3, 500)

    # Define neighbors
    p1.neighbors = [p2, p3]
    p2.neighbors = [p1, p3]
    p3.neighbors = [p1, p2]

    # Initialize network
    network = Network([p1, p2, p3])

    # Simulate transactions
    p1.send_money(p2, 10)
    p2.send_money(p3, 20)
    p3.send_money(p1, 25)

    # Initiate snapshot
    network.initiate_snapshot(1)

    # Continue transactions
    p1.send_money(p2, 20)
    p2.send_money(p3, 30)
    p3.send_money(p1, 35)

    # Print network state
    print(network)
