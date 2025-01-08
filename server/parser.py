import socket

# COMMANDS
DOWNLOAD = 1
UPLOAD = 2
LIST = 3
DELETE = 4
NOTIFY = 5

# ACKNOWLEDGEMENT VALUES
OK = 10
NOK = 11


def receive_package(sock: socket.socket) -> str:
    length_prefix = sock.recv(4)
    data_length = int.from_bytes(length_prefix, "big")
    data = sock.recv(data_length)
    data = data.decode()
    return data


def send_package(sock: socket.socket, size: int, data: str) -> None:
    length_prefix = size.to_bytes(4, "big")
    data_b = data.encode()
    data_packet = length_prefix + data_b
    sock.send(data_packet)


def send_command(sock: socket.socket, cmd: int) -> None:
    sock.send(cmd.to_bytes(4, "big"))


def receive_command(sock: socket.socket) -> int:
    cmd = sock.recv(4)
    return int.from_bytes(cmd, "big")


def send_acknowledgement(sock: socket.socket, val: int) -> None:
    sock.send(val.to_bytes(2, "big"))


def receive_acknowledgement(sock: socket.socket) -> int:
    val = sock.recv(2)
    return int.from_bytes(val, "big")
