import socket
import threading
import json


class Server:
    def __init__(self, host="localhost", port=5000):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.clients = {}
        self.snapshots = []
        self.total_markers = 0
        self.total_marker = {1: 0, 2: 0, 3: 0}
        self.snaps = {1: [], 2: [], 3: []}
        self.snap_credit = {1 : 0,2 : 0,3 : 0}

    def handle_backup(self, client, addr):
        while True:
            try:
                data = client.recv(1024).decode("utf-8")
                if data:
                    snap_data = json.loads(data)
                    # Here you can use the data received from the backup server
                    print(f"Received data from backup server: {snap_data}")
            except Exception as e:
                print(f"Error handling backup server {addr}: {e}")
                break

        client.close()
        print(f"Backup server {addr} disconnected")

    def handle_client(self, client, addr):
        while True:
            try:
                snapshot = client.recv(1024).decode("utf-8")
                if snapshot:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect(("localhost", 6000))  # Assuming the backup server is on localhost:6000
                        s.sendall(snapshot.encode("utf-8"))
                    snap_data = json.loads(snapshot)
                    state = snap_data["state"]
                    id = snap_data["id"]
                    self.snaps[id] = snapshot
                    self.snap_credit[id] = int(state)
                    #print(f"{self.snap_credit[id]},{state}")
                    self.total_marker[id] = 1
                    #print(f"State: {state}, ID: {id}")
                    #print(f"{self.total_marker[id]}")
                    if(self.total_marker[1] == 1 and self.total_marker[2] == 1 and self.total_marker[3] == 1):
                        total = self.snap_credit[1] + self.snap_credit[2] + self.snap_credit[3]
                        print(f"Received snapshot: {total}")
                        print(f"{self.snaps[1]}")
                        print(f"{self.snaps[2]}")
                        print(f"{self.snaps[3]}")
                        self.total_marker[1] = 0
                        self.total_marker[2] = 0
                        self.total_marker[3] = 0
                    #self.snapshots.append(snap_data)
            except Exception as e:
                print(f"Error handling client {addr}: {e}")
                break

        client.close()
        print(f"Client {addr} disconnected")
        del self.clients[addr]

    def start(self):
        #server = socket.gethostbyname(socket.gethostname())
        #server_address = ("localhost", 5050)
        #self.server.bind(server_address)
        self.server.listen()
        print("Server started...")
        while True:
            client, addr = self.server.accept()
            #self.server.bind(addr)

            print(f"New connection {addr}")
            self.clients[addr] = client
            #print(f"{self.clients[addr]},{addr}")
            if addr[0] == "localhost" and addr[1] == 6000:  # Assuming the backup server is on localhost:6000
                client_thread = threading.Thread(target=self.handle_backup, args=(client, addr))
            else:
                client_thread = threading.Thread(target=self.handle_client, args=(client, addr))
            # client_thread = threading.Thread(
            #     target=self.handle_client, args=(client, addr)
            # )
            client_thread.start()


if __name__ == "__main__":
    Server().start()
