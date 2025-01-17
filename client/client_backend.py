import re
import socket
import os
import sys
import threading
from parser import *

'''Throughout the code data transfer is done through a convention which is sending 
the packet size before sending the meaningfuldata. Initial data sent for packet size
 is always 4 bytes in big endian. This functionality is implemented in the parser.py file and imported here'''

class Client:

    def __init__(self):
        self.host = None
        self.port = None
        self.alias = None
        self.sock = None
        self.ui_update_callback = None
        self.sock_data_transfer = None
        self.file = None
        self.file_size = 0
        self.open_client_user_interface = None

    
    def connect(self):
        try:
            # Initialize socket and connect to the server
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.connect((self.host, self.port))

            self.sock.send(self.alias.encode())
            response = receive_acknowledgement(self.sock)

            if response == NOK:
                print(f"Username already taken: {self.alias}")
                self.sock.close()
                self.ui_update_callback("ERROR", "USERNAME_TAKEN")
                sys.exit(1)
            elif response == OK:
                print(f"Connection successfully established")
                self.open_client_user_interface()

            print(response)

            # Start listener thread
            t = threading.Thread(target=self.listen_server, args=())
            t.start()

        except Exception as e:
            print(f"Error: {e}")
            self.ui_update_callback("ERROR", "CONNECTION_ERROR")

    '''This function listens to the server all the time. This listening process is done through the first socket which
    is only for command handling.'''

    '''After request function is called and server is informed this function captures a response from server and the 
    necessary actions for command starts after this point. This request-response is basically a handshake before every command
    to ensure both client and server is ready.'''
    def listen_server(self):
        while True:
            try:
                command = receive_command(self.sock)
                if command == DOWNLOAD:
                    self.handle_download_file_response()
                elif command == UPLOAD:
                    self.handle_upload_file_response()
                elif command == LIST:
                    self.handle_get_file_list_response()
                elif command == DELETE:
                    self.handle_delete_file_response()
                elif command == NOTIFY:
                    self.handle_notify_response()
            except Exception as e:
                self.ui_update_callback("LOG", f"Server connection lost!")
                self.ui_update_callback("ERROR", "CONNECTION_LOST")
                break

    ''' According to the command given by client, client calls the regarding request function, each request
      function informs the server about the action client wants to do.'''
    def handle_command(self, command, data):
        if command == DOWNLOAD:
            self.send_download_file_request(data)
        elif command == UPLOAD:
            self.send_upload_file_request(data)
        elif command == LIST:
            self.send_get_file_list_request()
        elif command == DELETE:
            self.send_delete_file_request(data)

    def send_delete_file_request(self, file_name):
        send_command(self.sock, DELETE)
        send_package(self.sock, len(file_name), file_name)

    def handle_delete_file_response(self):
        response = receive_acknowledgement(self.sock)

        if response == OK:
            self.ui_update_callback(DELETE, True)
        elif response == NOK:
            self.ui_update_callback(DELETE, False)

    def send_get_file_list_request(self):
        send_command(self.sock, LIST)

    def handle_get_file_list_response(self):
        files_info = receive_package(self.sock)
        print("\n")
        permanent_file_registry = self.permanent_file_registry_load(files_info)
        self.ui_update_callback(LIST, permanent_file_registry)

    def send_upload_file_request(self,file_path):
        send_command(self.sock, UPLOAD)
        try:
            file, file_name, file_size, file_name_size = self.file_util(file_path)
            self.file = file
            self.file_size = file_size

            send_package(self.sock, file_name_size, file_name)

            file_size_len = len(str(file_size))
            send_package(self.sock, file_size_len, str(file_size))

        except Exception as e:
            print(f"exception {e}")
    
    def handle_upload_file_response(self):
        try:
            ''' Second socket for data transfer is initialized and used to connect to the server. After 
            data transfer is over it is closed.'''
            self.sock_data_transfer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock_data_transfer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
            self.sock_data_transfer.connect((self.host, self.port+1))

            bytes_sent = 0
            while bytes_sent < self.file_size:
                data = self.file.read(4096)
                if not data:
                    break
                self.sock_data_transfer.sendall(data)
                bytes_sent += len(data)
        except Exception as e:
            print(e)
        finally:
            self.sock_data_transfer.close()
            self.send_get_file_list_request()

    ''' This function is only called when client wants to upload a file. send_upload_file_request calls this function.
    Necessary file actions are done before uploading the file'''
    def file_util(self, file_path):
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError("File does not exist")

            file = open(file_path, "rb")
            file_name = os.path.basename(file_path)

            file_size = os.path.getsize(file_path)
            file_name_size = len(file_name)

            print(f"file_name_size = {file_name_size}")
            print(f"file_size: {file_size}")

            return file, file_name, file_size, file_name_size
        except Exception as e:
            print(f"Error: {e}")
            return None

    def send_download_file_request(self, file_name):
        send_command(self.sock, DOWNLOAD)

        file_name_size = len(file_name)
        send_package(self.sock, file_name_size, file_name)

    def handle_download_file_response(self):
        '''Second socket for file transfer is opened and connected'''
        self.sock_data_transfer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_data_transfer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        self.sock_data_transfer.connect((self.host, self.port+1))

        file_name = receive_package(self.sock)
        file_name = file_name.split("_")[1]
        file_size = int(receive_package(self.sock))

        with open(f"{file_name}", "wb") as f:
            bytes_received = 0
            while bytes_received < file_size:
                data = self.sock_data_transfer.recv(4096)
                if not data:
                    break
                f.write(data)
                bytes_received += len(data)

        print(f"file completely downloaded")
        self.sock_data_transfer.close()


    '''For response there is no request but only handling response. Since sending the notification request comes
    from the server unlike other commands'''
    def handle_notify_response(self):

        downloader_name = receive_package(self.sock)
        file_name = receive_package(self.sock)

        print(f"\n{downloader_name} downloaded your file named {file_name}!")
        self.ui_update_callback("LOG", f"{downloader_name} downloaded your file named {file_name.split('_')[1]}!")

    '''This function is for when server shutdowns and reinstantiated it starts from state when it was shutdown.
    It reads the permanent-file-registry txt file and populates it inner map structure from it.'''
    def permanent_file_registry_load(self, data):
        print(data)
        try:
            # Split the input into lines
            lines = data.strip().splitlines()

            result = {}
            current_client = None

            for line in lines:
                line = line.strip()
                if line.startswith("Client"):
                    # Extract the client's name (e.g., 'ece' or 'ege')
                    current_client = line.split()[1]
                    result[current_client] = []  # Initialize an empty list for this client
                elif line.startswith("{"):
                    # Extract filenames from the set notation
                    files = line.strip("{}").split(", ")
                    for file in files:
                        file = file.strip("'")  # Remove surrounding quotes
                        # Extract the meaningful part after the last underscore
                        meaningful_part = file.split('_')[-1]
                        if meaningful_part not in result[current_client]:
                            result[current_client].append(meaningful_part)

            return result
        except Exception as e:
            print(f"Error reading registry: {e}")


if __name__ == "__main__":
    my_client = Client()
    my_client.connect()
