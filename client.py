import socket

HOST = "127.0.0.1"
PORT = 9876

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))

    data = input("enter your data: ")
    s.sendall(data.encode())

    data = s.recv(1024)

print(f"Received: {data.decode()}")