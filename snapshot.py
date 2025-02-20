import threading
import time
import queue as queue
import socket, pickle
import sys, select
import random
import pickle


creditQueue = queue.Queue()
debitQueue = queue.Queue()
exitQueue = queue.Queue()
snapshotQueue = queue.Queue()

name_info = {}
port_info = {}
ref_client_info = {}
port2client = {}
client2name = {}
snapshotIdValue = {}


class Message:
    def __init__(self, messageType, amountToTransfer, markerId, senderInfo):
        self.messageType = messageType
        self.amountToTransfer = amountToTransfer
        self.markerId = markerId
        self.senderInfo = senderInfo

    def getMessageType(self):
        return self.messageType

    def getAmountToTransfer(self):
        return self.amountToTransfer

    def getMarkerId(self):
        return self.markerId

    def getSenderInfo(self):
        return self.senderInfo


class Snapshot:
    def __init__(
        self,
        processState,
        markerId,
        count,
        channelOneReceived,
        channelTwoReceived,
        channelThreeReceived,
    ):
        self.processState = processState
        self.channelOne = queue.Queue()
        self.channelOneReceived = channelOneReceived
        self.channelTwo = queue.Queue()
        self.channelTwoReceived = channelTwoReceived
        self.channelThree = queue.Queue()
        self.channelThreeReceived = channelThreeReceived
        self.markerId = markerId
        self.count = count

    def getProcessState(self):
        return self.processState

    def getMarkerId(self):
        return self.markerId

    def getCount(self):
        return self.count

    def getChannelOne(self):
        return self.channelOne

    def getChannelTwo(self):
        return self.channelTwo

    def getChannelThree(self):
        return self.channelThree

    def getChannelOneReceived(self):
        return self.channelOneReceived

    def getChannelTwoReceived(self):
        return self.channelTwoReceived

    def getChannelThreeReceived(self):
        return self.channelThreeReceived

    def setChannelOne(self, channelOne):
        self.channelOne.put(channelOne)

    def setChannelTwo(self, channelTwo):
        self.channelTwo.put(channelTwo)

    def setChannelThree(self, channelThree):
        self.channelThree.put(channelThree)

    def setChannelOneReceived(self, channelOneReceived):
        self.channelOneReceived = channelOneReceived

    def setChannelTwoReceived(self, channelTwoReceived):
        self.channelTwoReceived = channelTwoReceived

    def setChannelThreeReceived(self, channelThreeReceived):
        self.channelThreeReceived = channelThreeReceived

    def setCount(self, count):
        self.count = count


def parse_file(filename, processName):
    f = open(filename, "r")
    count = 1
    for line in f:
        a = line.split()
        if a[0] == processName:
            name_info["server"] = processName
            port_info["server"] = int(a[1])
        else:
            name_info["client" + str(count)] = a[0]
            port_info["client" + str(count)] = int(a[1])
            count = count + 1
    ## To get the information about the client if we know the port number
    for key, value in port_info.items():
        port2client[str(value)] = key
    for key, value in name_info.items():
        client2name[str(value)] = key


def readBalance(filename="post_file.txt"):
    f = open(filename, "r")
    lines = f.readlines()
    balance = lines[0]
    print(str(balance))
    return balance


## Console thread only to get the information from console - Done
class console_thread(threading.Thread):
    def __init__(self, name, inputQueueLock, snapshotQueueLock):
        threading.Thread.__init__(self)
        self.name = name
        self.inputQueueLock = inputQueueLock
        self.snapshotQueueLock = snapshotQueueLock

    def run(self):
        global clientCount
        clientCount = 0
        while True:
            if sys.stdin.readline():
                line = sys.stdin.readline().strip()
                if line.split()[0] == "Snap":
                    self.snapshotQueueLock.acquire()
                    snapshotQueue.put("Snapshot")
                    self.snapshotQueueLock.release()
                elif line.split()[0] == "Quit":
                    exitQueue.put(line)
                    break
                else:
                    print((self.name).upper() + ": Invalid input")
            if not exitQueue.empty():
                break


class master_thread(threading.Thread):
    def __init__(
        self,
        name,
        amount,
        count,
        inputQueueLock,
        creditQueueLock,
        debitQueueLock,
        snapshotQueueLock,
        markerCount,
    ):
        threading.Thread.__init__(self)
        self.name = name
        self.amount = amount
        self.inputQueueLock = inputQueueLock
        self.creditQueueLock = creditQueueLock
        self.debitQueueLock = debitQueueLock
        self.snapshotQueueLock = snapshotQueueLock
        self.count = count
        self.markerCount = markerCount

    def run(self):
        while True:
            ## 1. send amount/marker 2. receive amount/marker 3. snapshot recording 4. exit queue check
            ## Receive message/ marker
            while not creditQueue.empty():
                self.creditQueueLock.acquire()
                incomingMessage = creditQueue.get()
                self.creditQueueLock.release()
                ## if message is received 1. update the balance 2. Record channel state if recording is on
                if incomingMessage.getMessageType() == "MESSAGE":
                    self.amount += incomingMessage.getAmountToTransfer()
                    print(
                        (self.name).upper()
                        + ": Amount "
                        + str(incomingMessage.getAmountToTransfer())
                        + " received from "
                        + incomingMessage.getSenderInfo().upper()
                    )
                    print(
                        (self.name).upper()
                        + ": Balance after credit is "
                        + str(self.amount)
                    )
                    clientName = client2name[incomingMessage.getSenderInfo()]
                    if bool(snapshotIdValue):
                        for key, value in snapshotIdValue.items():
                            if (
                                clientName == "client1"
                                and value.getChannelOneReceived() == False
                            ):
                                value.setChannelOne(
                                    incomingMessage.getAmountToTransfer()
                                )
                            elif (
                                clientName == "client2"
                                and value.getChannelTwoReceived() == False
                            ):
                                value.setChannelTwo(
                                    incomingMessage.getAmountToTransfer()
                                )
                            elif (
                                clientName == "client3"
                                and value.getChannelThreeReceived() == False
                            ):
                                value.setChannelThree(
                                    incomingMessage.getAmountToTransfer()
                                )
                            snapshotIdValue[key] = value

                elif incomingMessage.getMessageType() == "MARKER":
                    ## 1. I am the marker initiator. Hence the markers mark the stop. 1.1 All channels have received the marker - Stop recording and output the snapshot and remove from snapshot queue 1.2 All channels have not received. Stop recording for the received channel only 2. Someone else requests record and create snapshot object and send marker in outgoing channels

                    markerId = incomingMessage.getMarkerId()
                    if markerId in snapshotIdValue.keys():
                        snapshot = snapshotIdValue[markerId]
                        snapshot.setCount(snapshot.getCount() + 1)
                        if snapshot.getCount() == 3:
                            sender = snapshot.getMarkerId()[:-1].upper()
                            clientName = client2name[incomingMessage.getSenderInfo()]
                            print(
                                "Marker"
                                + snapshot.getMarkerId()
                                + " received from "
                                + name_info[clientName].upper()
                            )
                            outputFile = open("output.txt", "a")
                            print(
                                "________________________________________________________"
                            )
                            print(
                                (self.name).upper()
                                + ": Snapshot recording completed. Snapshot Id :"
                                + snapshot.getMarkerId()
                                + " initiated by "
                                + sender
                            )
                            outputFile.write(
                                (self.name).upper()
                                + ": Snapshot recording completed. Snapshot Id :"
                                + snapshot.getMarkerId()
                                + " initiated by "
                                + sender
                                + "\n"
                            )
                            print(
                                (self.name).upper()
                                + ": Process State : "
                                + str(snapshot.getProcessState())
                            )
                            outputFile.write(
                                (self.name).upper()
                                + ": Process State : "
                                + str(snapshot.getProcessState())
                                + "\n"
                            )

                            print(
                                (self.name).upper()
                                + ": Channel "
                                + name_info["client1"].upper()
                                + " to "
                                + self.name.upper()
                                + " state : "
                                + str(snapshot.getChannelOne().queue)
                            )
                            outputFile.write(
                                (self.name).upper()
                                + ": Channel "
                                + name_info["client1"].upper()
                                + " to "
                                + self.name.upper()
                                + " state : "
                                + str(snapshot.getChannelOne().queue)
                                + "\n"
                            )
                            print(
                                (self.name).upper()
                                + ": Channel "
                                + name_info["client2"].upper()
                                + " to "
                                + self.name.upper()
                                + " state : "
                                + str(snapshot.getChannelTwo().queue)
                            )
                            outputFile.write(
                                (self.name).upper()
                                + ": Channel "
                                + name_info["client2"].upper()
                                + " to "
                                + self.name.upper()
                                + " state : "
                                + str(snapshot.getChannelTwo().queue)
                                + "\n"
                            )
                            print(
                                (self.name).upper()
                                + ": Channel "
                                + name_info["client3"].upper()
                                + " to "
                                + self.name.upper()
                                + " state : "
                                + str(snapshot.getChannelThree().queue)
                            )
                            outputFile.write(
                                (self.name).upper()
                                + ": Channel "
                                + name_info["client3"].upper()
                                + " to "
                                + self.name.upper()
                                + " state : "
                                + str(snapshot.getChannelThree().queue)
                                + "\n"
                            )
                            del snapshotIdValue[markerId]
                            print(
                                "________________________________________________________"
                            )
                            outputFile.close()
                        else:
                            ##Stop recording in that channel and continue recording other channels
                            clientName = client2name[incomingMessage.getSenderInfo()]
                            print(
                                "Marker"
                                + snapshot.getMarkerId()
                                + " received from "
                                + name_info[clientName].upper()
                            )
                            if clientName == "client1":
                                snapshot.setChannelOneReceived(True)
                            elif clientName == "client2":
                                snapshot.setChannelTwoReceived(True)
                            else:
                                snapshot.setChannelThreeReceived(True)
                            snapshotIdValue[markerId] = snapshot

                    else:
                        ##create a new Snapshot for the new incoming request, mark that channel as empty and send markers on all other outgoing channels
                        print(
                            "********************************************************"
                        )
                        print(
                            (self.name).upper()
                            + ": Received Snapshot Request "
                            + incomingMessage.getSenderInfo().upper()
                        )
                        snapshot = Snapshot(
                            self.amount,
                            incomingMessage.getMarkerId(),
                            0,
                            False,
                            False,
                            False,
                        )
                        clientName = client2name[incomingMessage.getSenderInfo()]

                        if clientName == "client1":
                            snapshot.setChannelOneReceived(True)
                        elif clientName == "client2":
                            snapshot.setChannelTwoReceived(True)
                        elif clientName == "client3":
                            snapshot.setChannelThreeReceived(True)
                        snapshot.setCount(1)
                        snapshotIdValue[incomingMessage.getMarkerId()] = snapshot
                        self.debitQueueLock.acquire()
                        debitQueue.put(snapshot)
                        self.debitQueueLock.release()
                        self.markerCount += 1

            if clientCount == 3:
                self.count = self.count + 1
            if not exitQueue.empty():
                ## may not be needed
                if not debitQueue.empty() and isinstance(debitQueue.get(), Message):
                    self.debitQueueLock.acquire()
                    debit = debitQueue.get()
                    self.debitQueueLock.release()
                    print(
                        (self.name).upper()
                        + ": Latest transaction requests sent after quit reverted"
                    )
                    self.amount += debit.getAmountToTransfer()
                print(
                    (self.name).upper()
                    + ": Process exiting. Amount available "
                    + str(self.amount)
                )
                break

            ## Send money
            if clientCount == 3 and self.count == 400000:
                clientChosen = random.randint(1, 3)
                debitAmount = random.randint(1, 100)
                self.count = 0
                if self.amount - debitAmount > 0:
                    debitRequest = Message(
                        "MESSAGE", debitAmount, clientChosen, self.name
                    )
                    self.debitQueueLock.acquire()
                    debitQueue.put(debitRequest)
                    self.debitQueueLock.release()
                    self.amount = self.amount - debitAmount
                    print(
                        (self.name).upper()
                        + ": Sending amount to "
                        + (name_info["client" + str(clientChosen)]).upper()
                        + ", "
                        + str(debitAmount)
                    )
                    print(
                        (self.name).upper()
                        + ": Available balance is "
                        + str(self.amount)
                    )

            ## Send marker - Create Snapshot and add it to debit queue to send.
            while not snapshotQueue.empty():
                print("********************************************************")
                self.snapshotQueueLock.acquire()
                snapshotQueue.get()
                self.snapshotQueueLock.release()
                markerId = self.name + str(self.markerCount)
                snapshot = Snapshot(self.amount, markerId, 0, False, False, False)
                snapshotIdValue[markerId] = snapshot
                self.debitQueueLock.acquire()
                debitQueue.put(snapshot)
                self.debitQueueLock.release()
                self.markerCount += 1


class server_thread(threading.Thread):
    def __init__(self, name, port, debitQueueLock):
        threading.Thread.__init__(self)
        self.name = name
        self.port = port
        self.debitQueueLock = debitQueueLock

    def run(self):
        ## Invoke a server with the following port  and wait for all the connections to this server from other process
        self.invoke_server()
        ## Once all are connections made then the process waits for the input from console and sends it to the other process
        self.send_info()
        ## close the server socket at the process
        self.server_socket.close()

    ## Creating a server socket and waiting for the other clients to connectto it
    def invoke_server(self):
        server_socket = socket.socket()
        self.server_socket = server_socket
        server_socket.bind(("", self.port))
        server_socket.listen(5)

        self.client1, self.addr1 = server_socket.accept()
        self.client1_info = self.client1.recv(1024)
        connection_message = (
            (self.name).upper()
            + ": Connection between "
            + self.name
            + " and "
            + name_info[port2client[self.client1_info]]
            + " has been formed."
        )
        print(connection_message)
        # print ((self.name).upper()+ ": Connection between "+self.name + " and " + name_info[port2client[self.client1_info]] + " has been formed.")

        self.client2, self.addr2 = server_socket.accept()
        self.client2_info = self.client2.recv(1024)
        print(
            (self.name).upper()
            + ": Connection between "
            + self.name
            + " and "
            + name_info[port2client[self.client2_info]]
            + " has been formed."
        )

        self.client3, self.addr3 = server_socket.accept()
        self.client3_info = self.client3.recv(1024)
        print(
            (self.name).upper()
            + ": Connection between "
            + self.name
            + " and "
            + name_info[port2client[self.client3_info]]
            + " has been formed."
        )

        self.assign_clients()

    def assign_clients(self):
        ref_client_info[str(port2client[self.client1_info])] = self.client1
        ref_client_info[str(port2client[self.client2_info])] = self.client2
        ref_client_info[str(port2client[self.client3_info])] = self.client3

    def send_info(self):
        count = 0
        while True:
            ## Check if user requested quit
            if not exitQueue.empty():
                ref_client_info["client1"].send(
                    pickle.dumps(Message("QUIT", 0, 0, self.name))
                )
                ref_client_info["client2"].send(
                    pickle.dumps(Message("QUIT", 0, 0, self.name))
                )
                ref_client_info["client3"].send(
                    pickle.dumps(Message("QUIT", 0, 0, self.name))
                )
                break

            ## Send money/marker to the client
            while not debitQueue.empty() and clientCount == 3:
                time.sleep(1)
                self.debitQueueLock.acquire()
                debitInfo = debitQueue.get()
                self.debitQueueLock.release()
                if isinstance(debitInfo, Message):
                    clientInfo = "client" + str(debitInfo.getMarkerId())
                    debitAmount = debitInfo.getAmountToTransfer()
                    clientName = name_info[clientInfo]
                    ref_client_info[clientInfo].send(
                        pickle.dumps(Message("MESSAGE", debitAmount, 0, self.name))
                    )
                    print(
                        (self.name).upper()
                        + ": Amount "
                        + str(debitAmount)
                        + " sent to "
                        + str(clientName).upper()
                    )
                elif isinstance(debitInfo, Snapshot):
                    print("Sending marker to others: " + debitInfo.getMarkerId())
                    ref_client_info["client1"].send(
                        pickle.dumps(
                            Message("MARKER", 0, debitInfo.getMarkerId(), self.name)
                        )
                    )
                    ref_client_info["client2"].send(
                        pickle.dumps(
                            Message("MARKER", 0, debitInfo.getMarkerId(), self.name)
                        )
                    )
                    ref_client_info["client3"].send(
                        pickle.dumps(
                            Message("MARKER", 0, debitInfo.getMarkerId(), self.name)
                        )
                    )


class client_thread(threading.Thread):
    def __init__(self, name, port, creditQueueLock):
        threading.Thread.__init__(self)
        self.name = name
        self.port = port
        self.creditQueueLock = creditQueueLock

    def run(self):
        self.invoke_client()
        self.get_info()
        self.client_socket.close()

    def invoke_client(self):
        client_socket = socket.socket()
        global clientCount
        while True:
            try:
                client_socket.connect(("127.0.0.1", self.port))
                # print(bytes([port_info['server']]).size())
                # client_socket.send([port_info['server']])


				# is port_info["server"] empty ?


                client_socket.send(pickle.dumps([port_info["server"]]))
                print(port_info[""])
                break
            except socket.error as msg:
                continue
        self.client_socket = client_socket
        clientCount += 1

    def get_info(self):
        while True:
            recvd = self.client_socket.recv(1024)
            print("_____")
            print(recvd)  # console output
            recvdMessage = pickle.loads(recvd)
            if recvdMessage.getMessageType() == "QUIT":
                exitQueue.put("Quit")
                break
            ##time.sleep(1)
            self.creditQueueLock.acquire()
            creditQueue.put(recvdMessage)
            self.creditQueueLock.release()


def process(argv):
    parse_file(sys.argv[2], sys.argv[1])

    inputQueueLock = threading.RLock()
    creditQueueLock = threading.RLock()
    debitQueueLock = threading.RLock()
    snapshotQueueLock = threading.RLock()

    console = console_thread(name_info["server"], inputQueueLock, snapshotQueueLock)
    print(name_info["server"].upper() + ": The amount available is ")
    balance = readBalance(sys.argv[3])
    master = master_thread(
        name_info["server"],
        int(balance),
        0,
        inputQueueLock,
        creditQueueLock,
        debitQueueLock,
        snapshotQueueLock,
        1,
    )
    server = server_thread(name_info["server"], port_info["server"], debitQueueLock)
    client1 = client_thread(name_info["client1"], port_info["client1"], creditQueueLock)
    client2 = client_thread(name_info["client2"], port_info["client2"], creditQueueLock)
    client3 = client_thread(name_info["client3"], port_info["client3"], creditQueueLock)

    console.start()
    master.start()
    server.start()
    client1.start()
    client2.start()
    client3.start()


if __name__ == "__main__":
    process(sys.argv)
