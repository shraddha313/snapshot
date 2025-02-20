import socket
import threading
import json
import time

class Master:
    def __init__(self, host="localhost", port=7000):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.servers = {}  # stores the primary and backup server details
        self.lease_expiration = time.time() + 60  # lease expires in 60 seconds

    def handle_server(self, server, addr):
        while True:
            try:
                data = server.recv(1024).decode("utf-8")
                if data:
                    data = json.loads(data)
                    # here you can handle the received data
                    print(f"Received data: {data}")
            except Exception as e:
                print(f"Error handling server {addr}: {e}")
                break

        server.close()
        print(f"Server {addr} disconnected")

    def elect_servers(self):
        # Here, we simply choose the first two servers as the primary and backup servers
        # In a real system, you would need a proper election algorithm
        servers = list(self.servers.keys())
        if len(servers) >= 2:
            self.servers[servers[0]] = 'primary'
            self.servers[servers[1]] = 'backup'

    def check_lease(self):
        while True:
            time.sleep(1)
            if time.time() > self.lease_expiration:
                print("Lease expired, triggering new election...")
                self.elect_servers()
                self.lease_expiration = time.time() + 60

    def start(self):
        self.server.listen()
        print("Master started...")

        lease_thread = threading.Thread(target=self.check_lease)
        lease_thread.start()

        while True:
            server, addr = self.server.accept()
            print(f"New server {addr}")
            self.servers[addr] = 'candidate'
            server_thread = threading.Thread(target=self.handle_server, args=(server, addr))
            server_thread.start()


if __name__ == "__main__":
    Master().start()
