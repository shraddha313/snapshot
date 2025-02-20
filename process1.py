import client1

if __name__ == "__main__":
    client1.Process(1, 100, 5001, [5002, 5003], ("localhost", 5000),("localhost",5050),1).start()
