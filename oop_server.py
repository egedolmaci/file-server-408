import re
import socket
import threading
import time
import os
from parser import *

'''
The problems to be fixed:
- We need to add a mechanism to close all the running threads, and dependent threads with a function to 
call this on event user closes the server console window.

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

        self.connected_clients = {}
        self.connected_clients_lock = threading.Lock()

        self.permanent_file_registry_lock = threading.Lock()

        self.save_files_path = "./files"

        self.log_to_console = None

    def start(self):
        if not os.path.exists(self.save_files_path):
            os.mkdir(self.save_files_path)

        # Check if 'test.txt' exists
        if not os.path.exists("permanent-file-registry"):
            # Create the file if it doesn't exist
            with open("permanent-file-registry", "w") as file:
                pass  # Creates an empty file
            print("permanent-file-registry created.")

        self.permanent_file_registry_load()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen()

            print(f"Server is running on: ({HOST}:{PORT})")
            self.log_to_console(f"Server is running on: ({HOST}:{PORT})")

            while True:
                conn, addr = s.accept()

                t = threading.Thread(target=self.client_connection, args=(conn, addr))
                t.start()

    def client_connection(self, conn, addr):
        print(f"new connection {addr}")
        self.log_to_console(f"new connection {addr}")

        alias = conn.recv(1024).decode()
        print(f"connected with {alias}")
        self.log_to_console(f"connected with {alias}")

        with self.connected_clients_lock:
            if alias in self.connected_clients.keys():
                print(f"Connection rejected for {alias} from {addr} since the username is already taken")
                send_acknowledgement(conn, NOK)
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

                    self.connected_clients[alias] = conn
                    print(f"connected by: {addr} with username {alias}")
                    send_acknowledgement(conn, OK)

        try:
            self.handle_command(alias, conn)
        except Exception as e:
            print(f"Client disconnceted {e}")
            self.connected_clients.pop(alias)

    def handle_command(self, alias, conn):
        while True:
            command = receive_command(conn)
            if command == DOWNLOAD:
                self.client_file_download(alias, conn)
            elif command == UPLOAD:
                self.client_file_upload(alias, conn)
            elif command == LIST:
                self.client_file_list(conn)
            elif command == DELETE:
                self.client_file_delete(alias, conn)

    def client_file_delete(self, alias, conn):
        file_name = receive_package(conn)
        file_owner = file_name.split("_")[0]

        if alias == file_owner:
            os.remove(f"{self.save_files_path}/{file_name}")
            self.client_file_registry[alias].remove(file_name)
            self.permanent_file_registry_save()
            send_command(conn, DELETE)
            send_acknowledgement(conn, OK)

        else:
            print("This is not the file owner")
            send_command(conn, DELETE)
            send_acknowledgement(conn, NOK)

    def client_file_upload(self, alias, conn):

        file_name = receive_package(conn)
        file_size = int(receive_package(conn))
        print(f"file size: {file_size}")

        with open(f"{self.save_files_path}/{alias}_{file_name}", "wb") as f:
            bytes_received = 0
            while bytes_received < file_size:
                data = conn.recv(4096)
                if not data:
                    break
                f.write(data)
                bytes_received += len(data)

        with self.client_file_registry_lock:
            self.client_file_registry[alias].add(f"{alias}_{file_name}")
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

    def client_file_list(self, conn):
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

                files_on_server_length = len(files_on_server)
                send_command(conn, LIST)
                send_package(conn, files_on_server_length, files_on_server)

    def client_file_download(self, alias, conn):

        file_name = receive_package(conn)
        print(f"file Name: {file_name}")

        file_owner = file_name.split("_")[0]

        try:
            with open(f"{self.save_files_path}/{file_name}", "rb") as file:
                file_size = os.path.getsize(f"{self.save_files_path}/{file_name}")
                file_name_len = len(str(file_name))
                file_size_len = len(str(file_size))

                send_command(conn, DOWNLOAD)
                send_package(conn, file_name_len, str(file_name))
                send_package(conn, file_size_len, str(file_size))

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
                if file_owner != alias:
                    if file_owner in self.connected_clients.keys():
                        downloader_name_len = len(str(alias))

                        send_command(self.connected_clients[file_owner], NOTIFY)
                        send_package(self.connected_clients[file_owner], downloader_name_len, str(alias))
                        send_package(self.connected_clients[file_owner], file_name_len, str(file_name))

        except Exception as e:
            print(f"error {e}")

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