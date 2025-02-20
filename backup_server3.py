import socket
import threading
import json

class BackupServer:
    def __init__(self, host="localhost", port=6000):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.snapshots = {}
        self.wake = 0

    def handle_client(self, client, addr):
        while True:
            # command = input()
            # if command == 's':
            #     self.wake = 1
            try:
                snapshot = client.recv(1024).decode("utf-8")
                
                if snapshot:
                    snap_data = json.loads(snapshot)
                    print(f"{snap_data}")
                    self.snapshots[addr] = snap_data

                    if ("main_wakeup" in snap_data and snap_data["main_wakeup"] == 1) or self.wake:
                        # If the main_wakeup bit is 1, send the data to the main server
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.connect(("localhost", 5000))  # Assuming the main server is on localhost:5000
                            s.sendall(json.dumps(self.snapshots[addr]).encode("utf-8"))
                            self.wake = 0
            except Exception as e:
                print(f"Error handling client {addr}: {e}")
                break

        client.close()
        print(f"Client {addr} disconnected")


    def input_thread(self, client, addr):
        while True:
            command = input()
            if command == 's':
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(("localhost", 5000))  # Assuming the main server is on localhost:5000
                    s.sendall(json.dumps(self.snapshots[addr]).encode("utf-8"))

    def start(self):
        self.server.listen()
        print("Backup server started...")
        while True:
            client, addr = self.server.accept()
            print(f"New connection {addr}")
            client_thread = threading.Thread(target=self.handle_client, args=(client, addr))
            threading.Thread(target=self.input_thread,args=(client, addr)).start()
            client_thread.start()

if __name__ == "__main__":
    BackupServer().start()
