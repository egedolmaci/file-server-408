import socket
import os
import sys
import threading
from parser import *

HOST = "127.0.0.1"
PORT = 9876


class Client:

    def __init__(self):
        self.host = HOST
        self.port = PORT
        self.alias = None
        self.sock = None

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))

            self.sock.send(self.alias.encode())

            response = receive_acknowledgement(self.sock)

            if response == NOK:
                print(f"Username already taken: {self.alias}")
                self.sock.close()
                sys.exit(1)
            elif response == OK:
                print(f"Connection successfully established")

            print(response)

            # Start listener thread
            t = threading.Thread(target=self.listen_server, args=())
            t.start()

            self.handle_command()

        except Exception as e:
            print(f"Error: {e}")

    def listen_server(self):
        while True:
            command = receive_command(self.sock)
            if command == DOWNLOAD:
                self.handle_download_file_response()
            elif command == LIST:
                self.handle_get_file_list_response()
            elif command == DELETE:
                self.handle_delete_file_response()
            elif command == NOTIFY:
                self.handle_notify_response()

    def handle_command(self, command):
        if command == DOWNLOAD:
            self.send_download_file_request()
        elif command == UPLOAD:
            self.send_upload_file_request()
        elif command == LIST:
            self.send_get_file_list_request()
        elif command == DELETE:
            self.send_delete_file_request()

    def send_delete_file_request(self):
        send_command(self.sock, DELETE)
        file_name = input("Please enter the file you want to delete: ")
        send_package(self.sock, len(file_name), file_name)

    def handle_delete_file_response(self):
        response = receive_acknowledgement(self.sock)

        if response == OK:
            print("File deleted successfully!")
        elif response == NOK:
            print("File could not be deleted you don't own this file!")

    def send_get_file_list_request(self):
        send_command(self.sock, LIST)

    def handle_get_file_list_response(self):
        files_info = receive_package(self.sock)
        print("\n")
        print(files_info)

    def send_upload_file_request(self):
        send_command(self.sock, UPLOAD)
        try:
            file, file_name, file_size, file_name_size = self.handle_upload_file_request()

            send_package(self.sock, file_name_size, file_name)

            file_size_len = len(str(file_size))
            send_package(self.sock, file_size_len, str(file_size))

            bytes_sent = 0
            while bytes_sent < file_size:
                data = file.read(4096)
                if not data:
                    break
                self.sock.sendall(data)
                bytes_sent += len(data)
        except Exception as e:
            print(f"exception {e}")

    def handle_upload_file_request(self):
        try:
            file_path = input("Please enter the file you want to send: ")

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
            print("merhaba")
            print(f"Error: {e}")
            return None

    def send_download_file_request(self):
        send_command(self.sock, DOWNLOAD)
        file_name = input("Please enter the file you want to download: ")

        file_name_size = len(file_name)
        send_package(self.sock, file_name_size, file_name)

    def handle_download_file_response(self):

        file_name = receive_package(self.sock)
        file_size = int(receive_package(self.sock))

        with open(f"{file_name}", "wb") as f:
            bytes_received = 0
            while bytes_received < file_size:
                data = self.sock.recv(4096)
                if not data:
                    break
                f.write(data)
                bytes_received += len(data)

        print(f"file completely downloaded")

    def handle_notify_response(self):

        downloader_name = receive_package(self.sock)
        file_name = receive_package(self.sock)

        print(f"\n{downloader_name} downloaded your file named {file_name}!")


if __name__ == "__main__":
    my_client = Client()
    my_client.connect()
