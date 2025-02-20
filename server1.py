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

    # def handle_client(self, client, addr):
    #     while True:
    #         try:
    #             snapshot = client.recv(1024).decode("utf-8")
    #             if not snapshot:
    #                 print(f"Client {addr} disconnected")
    #                 del self.clients[addr]
    #                 break
    #             print(f"Received snapshot: {snapshot}")
    #             self.snapshots.append(json.loads(snapshot))
    #         except Exception as e:
    #             print(f"Error handling client {addr}: {e}")
    #             del self.clients[addr]
    #             break
    def handle_client(self, client, addr):
        while True:
            try:
                snapshot = client.recv(1024).decode("utf-8")
                if snapshot:
                    print(f"Received snapshot: {snapshot}")
                    self.snapshots.append(json.loads(snapshot))
            except Exception as e:
                print(f"Error handling client {addr}: {e}")
                break

        client.close()
        print(f"Client {addr} disconnected")
        del self.clients[addr]

    def start(self):
        self.server.listen()
        print("Server started...")
        while True:
            client, addr = self.server.accept()
            print(f"New connection {addr}")
            self.clients[addr] = client
            client_thread = threading.Thread(
                target=self.handle_client, args=(client, addr)
            )
            client_thread.start()


if __name__ == "__main__":
    Server().start()
