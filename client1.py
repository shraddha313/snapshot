import socket
import threading
import random
import time
import json
import keyboard


class Process:
    def __init__(self, id, initial_balance, port, other_ports, server_address,secondry_server_address,cordinat):
        self.id = id
        self.balance = initial_balance
        self.state = initial_balance
        self.channel_state = {}
        self.recording = False
        self.port = port
        self.other_ports = other_ports
        self.server_address = server_address
        self.secondry_server_address = secondry_server_address
        self.cordinat = cordinat

    def send_money(self, amount, port):
        #for _ in range(3):  # Try to connect 3 times
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(("localhost", port))
                    message = {"type": "transaction", "amount": amount}
                    s.sendall(json.dumps(message).encode("utf-8"))
                self.balance -= amount
                print(
                    f"Process {self.id} sent {amount} money. Remaining balance: {self.balance}"
                )
                #break
            except ConnectionRefusedError:
                print(f"Connection refused by Process at port {port}. Retrying...")
                time.sleep(2)  # Wait for 2 seconds before retrying

    def receive_money(self, message):
        amount = message["amount"]
        self.balance += amount
        print(
            f"Process {self.id} received {amount} money. Current balance: {self.balance}"
        )

    def send_marker(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("localhost", port))
            message = {"type": "marker"}
            s.sendall(json.dumps(message).encode("utf-8"))
            self.send_snapshot_to_server()

    def receive_marker(self):
        self.state = self.balance
        self.recording = True
        print(f"Process {self.id} started recording. State: {self.state}")
        self.send_snapshot_to_server()

    def send_snapshot_to_server(self):
        #time.sleep(1)  # add some delay to make sure server is ready
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            message = {
                    "id": self.id,
                    "state": self.state,
                    "channel_state": self.channel_state,
                }
            if(self.cordinat):
                s.connect(self.server_address)
                s.sendall(json.dumps(message).encode("utf-8"))
                print(f"Process {self.id} sent its snapshot to server. State: {self.state}")
                self.recording = False
            else:
                s.connect(self.secondry_server_address)
                s.sendall(json.dumps(message).encode("utf-8"))
                print(f"Process {self.id} sent its snapshot to backup server. State: {self.state}")
                self.recording = False


    def send_thread(self):
        while True:
            for port in self.other_ports:
                amount = random.randint(1, 10)
                self.send_money(amount, port)
                time.sleep(20)
            # if keyboard.is_pressed("s"):  # if 'snap' is pressed
            #     self.state = self.balance
            #     self.recording = True
            #     for port in self.other_ports:
            #         self.send_marker(port)
            #     time.sleep(20)

    def receive_thread(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("localhost", self.port))
            s.listen()
            while True:
                conn, addr = s.accept()
                with conn:
                    message = json.loads(conn.recv(1024).decode("utf-8"))
                    if message["type"] == "transaction":
                        self.receive_money(message)
                    elif message["type"] == "marker":
                        self.receive_marker()
                    elif message["type"] == "cord":
                        self.cordinat = message["id"]

    def input_thread(self):
        while True:
            command = input()
            if command == 's':
                self.state = self.balance
                self.recording = True
                for port in self.other_ports:
                    self.send_marker(port)
                #time.sleep(10)

    # def initial(self):
    #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #         s.connect(("localhost", port))

    def start(self):
        threading.Thread(target=self.send_thread).start()
        threading.Thread(target=self.receive_thread).start()
        threading.Thread(target=self.input_thread).start()  # start the input thread
        self.send_snapshot_to_server()

