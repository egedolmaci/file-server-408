import socket
import threading
import time 

HOST = "127.0.0.1"
PORT = 9876

client_dict = {}
client_dict_lock = threading.Lock()

# def handle_commands():
#     while True:
        # command = input("Enter a command: ")
        # if command == "list":
        #     with client_dict_lock:
        #         if not client_dict:
        #             print("No clients are connected")
        #         else:
        #             print("Clients connected:")
        #             for addr, info in client_dict.items():
        #                 print(f"Client {addr} - Connected at: {info['time']}")
            

def print_client_dict(data):
    with client_dict_lock:
        if not client_dict:
            print("No clients are connected")
        else:
            print("Clients connected:")
            for addr, info in client_dict.items():
                print(f"Client {addr} - Connected at: {info['time']}")


def client_connection(conn, addr):
    with conn:
        with client_dict_lock:
            client_dict[addr] = {
                "connection": conn,
                "time": time.strftime("%H:%M:%S")
            }
        print(f"connected by: {addr}")

        while True:
            data = conn.recv(1024)
            if not data:
                break

            readible_data = data.decode()
            if readible_data == "list":
                print_client_dict(data.decode())

            print(f"data received from {addr} is {readible_data}")
            conn.sendall(data)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()

    print(f"Server is running on: ({HOST}:{PORT})")

    # t = threading.Thread()
    # t.start()

    while True:
        conn, addr = s.accept()

        t = threading.Thread(target=client_connection, args=(conn, addr), daemon=True)
        t.start()
    