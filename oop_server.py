import socket
import threading
import time 
import os

'''
The last problem is os.mkdir() cannot create the same dir over and over and raises exception to fix that
check if directory exists before and do not create new if it already exists


'''



HOST = "127.0.0.1"
PORT = 9876

class Server:
    
    def __init__(self):
        self.host = HOST
        self.port = PORT

        self.client_conn_history = {}
        self.client_conn_history_lock = threading.Lock()

        self.client_file_registry = {}
        self.client_file_registry_lock = threading.Lock()

        self.permanent_file_registry_lock = threading.Lock()

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen()

            print(f"Server is running on: ({HOST}:{PORT})")

            while True:
                conn, addr = s.accept()

                t = threading.Thread(target=self.client_connection, args=(conn, addr))
                t.start()
    
    def client_connection(self, conn, addr):
        print(f"new connection {addr}")

        alias = conn.recv(1024).decode()
        print(f"connected with {alias}")

        with self.client_file_registry_lock:
            if alias in self.client_file_registry:
                print(f"Connection rejected for {alias} from {addr} since the username is already taken")
                conn.send(b"Bad")
                conn.close()
                exit(1)
            else:
                self.client_file_registry[alias] = set()
                self.permanent_file_registry()

                with self.client_conn_history_lock:
                    self.client_conn_history[addr] = {
                        "connection": conn,
                        "time": time.strftime("%H:%M:%S")
                    }

                print(f"connected by: {addr} with username {alias}")
                conn.send(b"Good")

        self.handle_command(alias, conn)

    def handle_command(self, alias, conn):
        while True:
            command = conn.recv(4).decode()
            if command == "1":
                self.client_file_download(alias, conn)
            elif command == "2":
                self.handle_messages(alias, conn)
            elif command == "3":
                self.print_files()

    def handle_messages(self, alias, conn):

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

            with open(f"s_{file_name.decode()}", "wb") as f:
                bytes_received = 0
                while bytes_received < file_size:
                    data = conn.recv(4096)
                    if not data:
                        break
                    f.write(data)
                    bytes_received += len(data)

            with self.client_file_registry_lock:
                self.client_file_registry[alias].add(file_name.decode())
            self.permanent_file_registry()

            print(f"File successfully created")

    def print_history(self):
        with self.client_conn_history_lock:
            if not self.client_conn_history:
                print("No clients are connected")
            else:
                print("Clients connected:")
                for addr, info in self.client_conn_history.items():
                    print(f"Client {addr} - Connected at: {info['time']}") 
            
    def print_files(self):
        with self.client_file_registry_lock:
            if not self.client_file_registry:
                print("No files are uploaded to the server yet")
            else:
                print("Files Uploaded:")
                for user, file  in self.client_file_registry.items():
                    print(f"Client {user} - uploaded these files:")
                    print(file)

    def permanent_file_registry(self):
        with self.permanent_file_registry_lock:
            try:
                with open("permanent-file-registry", 'w') as file:
                    for key, value in self.client_file_registry.items():
                        file.write(f"{key}: {value}\n")
                print(f"Successfully written")
            except Exception as e:
                print(f"Error writing to file: {e}")
                
    def client_file_download(self, alias, conn):
        length_prefix = conn.recv(4)
        file_name_size = int.from_bytes(length_prefix, "big")
        print(f"file_name_size: {file_name_size}")

        file_name = conn.recv(file_name_size)
        print(f"file Name: {file_name.decode()}")

        with open(f"s_{file_name.decode()}", "rb") as file:
            file_size = os.path.getsize(file_name)
            
            file_size_len = len(str(file_size))
            length_prefix = file_size_len.to_bytes(4, "big")
            file_size_b = str(file_size).encode()
            file_size_packet = length_prefix + file_size_b
            conn.sendall(file_size_packet)

            print(f"file_size_size: {file_size_len}")
            print(f"file size = {str(file_size)}")

            bytes_sent = 0
            while bytes_sent < file_size:
                data = file.read(4096)
                if not data:
                    print(f"bytes sent: {bytes_sent}")
                    break
                conn.sendall(data)
                bytes_sent += len(data)


            print(f"file successfully sent")



        
            
















    
            
if __name__ == "__main__":
    my_server = Server()
    my_server.start()