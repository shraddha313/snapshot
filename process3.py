import client1

if __name__ == "__main__":
    client1.Process(3, 300, 5003, [5001, 5002], ("localhost", 5000),("localhost",5050),1).start()
