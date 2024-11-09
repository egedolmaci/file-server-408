import re
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

DOWNLOAD = "1"
UPLOAD = "2"
LIST = "3"


class Server:

    def __init__(self):
        self.host = HOST
        self.port = PORT

        self.client_conn_history = {}
        self.client_conn_history_lock = threading.Lock()

        self.client_file_registry = {}
        self.client_file_registry_lock = threading.Lock()

        self.connected_clients = []
        self.connected_clients_lock = threading.Lock()

        self.permanent_file_registry_lock = threading.Lock()

        self.save_files_path = "./files"

        self.permanent_file_registry_load()

        if not os.path.exists(self.save_files_path):
            os.mkdir("./files")


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

        with self.connected_clients_lock:
            if alias in self.connected_clients:
                print(f"Connection rejected for {alias} from {addr} since the username is already taken")
                conn.send(b"Bad")
                conn.close()
                exit(1)
            else:
                with self.client_file_registry_lock:
                    if alias not in self.client_file_registry.keys():
                        self.client_file_registry[alias] = set()
                        self.permanent_file_registry_save()

                    with self.client_conn_history_lock:
                        self.client_conn_history[addr] = {
                            "connection": conn,
                            "time": time.strftime("%H:%M:%S")
                        }

                    self.connected_clients.append(alias)
                    print(f"connected by: {addr} with username {alias}")
                    conn.send(b"Good")

        try:
            self.handle_command(alias, conn)
        except:
            self.connected_clients.remove(alias)

    def handle_command(self, alias, conn):
        while True:
            command = conn.recv(4).decode()
            if command == DOWNLOAD:
                self.client_file_download(alias, conn)
            elif command == UPLOAD:
                self.client_file_upload(alias, conn)
            elif command == LIST:
                self.print_files(conn)

    def client_file_upload(self, alias, conn):

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

            with open(f"{self.save_files_path}/{alias}_{file_name.decode()}", "wb") as f:
                bytes_received = 0
                while bytes_received < file_size:
                    data = conn.recv(4096)
                    if not data:
                        break
                    f.write(data)
                    bytes_received += len(data)

            with self.client_file_registry_lock:
                self.client_file_registry[alias].add(f"{alias}_{file_name.decode()}")
            self.permanent_file_registry_save()

            print(f"File successfully created")

    def print_history(self):
        with self.client_conn_history_lock:
            if not self.client_conn_history:
                print("No clients are connected")
            else:
                print("Clients connected:")
                for addr, info in self.client_conn_history.items():
                    print(f"Client {addr} - Connected at: {info['time']}")

    def print_files(self,conn):
        files_on_server = ""
        with self.client_file_registry_lock:
            if not self.client_file_registry:
                print("No files are uploaded to the server yet")
            else:
                print("Files Uploaded:")
                for user, file in self.client_file_registry.items():
                    print(f"Client {user} - uploaded these files:")
                    files_on_server += f"Client {user} - uploaded these files:\n"
                    print(file)
                    files_on_server += f"{file}\n"

                files_on_server_length = len(files_on_server).to_bytes(4,"big")
                conn.sendall(files_on_server_length)
                conn.sendall(files_on_server.encode())


    def permanent_file_registry_save(self):
        with self.permanent_file_registry_lock:
            try:
                with open("permanent-file-registry", 'w') as file:
                    for key, value in self.client_file_registry.items():
                        file.write(f"{key}: {value}\n")
                print(f"Successfully written")
            except Exception as e:
                print(f"Error writing to file: {e}")

    def permanent_file_registry_load(self):
        with self.permanent_file_registry_lock:
            try:
                with open("permanent-file-registry", 'r') as file:
                    for line in file:
                        line = line.strip()
                        if line:
                            # Regular expression to match the key and the set
                            match = re.match(r"(\w+): \{(.+)\}", line)
                            if match:
                                alias = match.group(1)  # Extract the key
                                # Process the set items, removing extra spaces and quotes
                                files = {item.strip().strip("'") for item in match.group(2).split(',')}
                                self.client_file_registry[alias] = files
            except Exception as e:
                print(f"Error reading registry: {e}")

    def client_file_download(self, alias, conn):
        length_prefix = conn.recv(4)
        file_name_size = int.from_bytes(length_prefix, "big")
        print(f"file_name_size: {file_name_size}")

        file_name = conn.recv(file_name_size)
        file_name = file_name.decode()
        print(f"file Name: {file_name}")

        try:
            with open(f"{self.save_files_path}/{file_name}", "rb") as file:
                file_size = os.path.getsize(f"{self.save_files_path}/{file_name}")

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
        except:
            print("error")

if __name__ == "__main__":
    my_server = Server()
    my_server.start()