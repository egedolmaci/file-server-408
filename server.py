import socket
import threading
import time 
import os

HOST = "127.0.0.1"
PORT = 9876

client_conn_history = {}
client_conn_history_lock = threading.Lock()

client_file_registry = {}
client_file_registry = threading.Lock()
file_storage_path = os.getcwd()



# def handle_commands():
#     while True:
        # command = input("Enter a command: ")
        # if command == "list":
        #     with client_conn_history_lock:
        #         if not client_conn_history:
        #             print("No clients are connected")
        #         else:
        #             print("Clients connected:")
        #             for addr, info in client_conn_history.items():
        #                 print(f"Client {addr} - Connected at: {info['time']}")
            

def print_client_conn_history(data):
    with client_conn_history_lock:
        if not client_conn_history:
            print("No clients are connected")
        else:
            print("Clients connected:")
            for addr, info in client_conn_history.items():
                print(f"Client {addr} - Connected at: {info['time']}")


def client_connection(conn, addr):
    with conn:
        with client_conn_history_lock:
            client_conn_history[addr] = {
                "connection": conn,
                "time": time.strftime("%H:%M:%S")
            }
        print(f"connected by: {addr}")

        while True:
            length_prefix = conn.recv(4)
            file_name_size = int.from_bytes(length_prefix, "big")

            print(f"file_name_size: {file_name_size}")

            file_name = conn.recv(file_name_size)
            print(f"file Name: {file_name.decode()}")

            length_prefix = conn.recv(4)
            file_size_size = int.from_bytes(length_prefix, "big")

            print(f"file_size_size: {file_size_size}")

            file_size = conn.recv(file_size_size)
            file_size = int(file_size.decode())
            print(f"file size: {file_size}")


            with open(f"received_{file_name}", "wb") as f:
                bytes_received = 0
                while bytes_received < file_size:
                    data = conn.recv(4096)
                    if not data:
                        break
                    f.write(data)
                    bytes_received += len(data)
                    print(f"Progress: {(bytes_received/file_size)*100:.2f}%")


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()

    print(f"Server is running on: ({HOST}:{PORT})")

    # t = threading.Thread()
    # t.start()

    while True:
        conn, addr = s.accept()

        t = threading.Thread(target=client_connection, args=(conn, addr))
        t.start()
    