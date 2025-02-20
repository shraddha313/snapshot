import socket
import threading
import random
import time
import json

def cordinate_thread():
        

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(("localhost", port))
                    message = {"type": "coed", "id": 1}