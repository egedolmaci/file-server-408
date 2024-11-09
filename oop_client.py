import socket
import os
import sys
import threading

DOWNLOAD = "1"
UPLOAD = "2"
LIST = "3"
DELETE = "4"
NOTIFY = "5"

HOST = "127.0.0.1"
PORT = 9876


class Client:

    def __init__(self):
        self.host = HOST
        self.port = PORT
        self.alias = None
        self.sock = None

    def connect(self):
        # TODO: send and receiving should be implemented with packet length
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))

            self.alias = input("What is the username: ")
            self.sock.send(self.alias.encode())

            response = self.sock.recv(1024).decode()

            if response == "Bad":
                print(f"Username already taken: {self.alias}")
                self.sock.close()
                sys.exit(1)
            elif response == "Good":
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
            command = self.sock.recv(4)
            command = command.decode()

            if command == DOWNLOAD:
                self.handle_download_file_response()
            elif command == LIST:
                self.handle_get_file_list_response()
            elif command == DELETE:
                self.handle_delete_file_response()
            elif command == NOTIFY:
                self.handle_notify_response()

    def handle_command(self):
        while True:
            command = input("Do you want to download(1), upload(2), list of files(3) or delete file(4)?")
            if command == DOWNLOAD:
                self.send_download_file_request()
            elif command == UPLOAD:
                self.send_upload_file_request()
            elif command == LIST:
                self.send_get_file_list_request()
            elif command == DELETE:
                self.send_delete_file_request()

    def send_delete_file_request(self):
        self.sock.send(DELETE.encode())
        file_name = input("Please enter the file you want to delete: ")
        file_name_size = len(file_name)

        length_prefix = file_name_size.to_bytes(4, "big")
        file_name_b = file_name.encode()
        file_name_packet = length_prefix + file_name_b
        self.sock.sendall(file_name_packet)

    def handle_delete_file_response(self):
        response = self.sock.recv(1024)
        response = response.decode()

        if response == "Good":
            print("File deleted successfully!")
        else:
            print("File could not be deleted you don't own this file!")

    def send_get_file_list_request(self):
        self.sock.send(LIST.encode())

    def handle_get_file_list_response(self):
        files_info_length_bytes = self.sock.recv(4)
        files_info_length = int.from_bytes(files_info_length_bytes, "big")

        files_info = self.sock.recv(files_info_length)
        files_info = files_info.decode()
        print(files_info)

    def send_upload_file_request(self):
        self.sock.send(UPLOAD.encode())

        try:
            file, file_name, file_size, file_name_size = self.handle_upload_file_request()

            length_prefix = file_name_size.to_bytes(4, "big")
            file_name = file_name.encode()
            file_name_packet = length_prefix + file_name
            self.sock.sendall(file_name_packet)

            file_size_len = len(str(file_size))
            length_prefix = file_size_len.to_bytes(4, "big")
            file_size_b = str(file_size).encode()
            file_size_packet = length_prefix + file_size_b
            self.sock.sendall(file_size_packet)

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
        self.sock.send(DOWNLOAD.encode())

        file_name = input("Please enter the file you want to download: ")
        file_name_size = len(file_name)

        length_prefix = file_name_size.to_bytes(4, "big")
        file_name_b = file_name.encode()
        file_name_packet = length_prefix + file_name_b
        self.sock.sendall(file_name_packet)

    def handle_download_file_response(self):

        length_prefix = self.sock.recv(4)
        file_name_size = int.from_bytes(length_prefix, "big")

        file_name = self.sock.recv(file_name_size)
        file_name = file_name.decode()

        length_prefix = self.sock.recv(4)
        file_size_size = int.from_bytes(length_prefix, "big")

        print(f"file_size_size: {file_size_size}")

        file_size = self.sock.recv(file_size_size)
        file_size = int(file_size.decode())
        print(f"file size: {file_size}")

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
        length_prefix = self.sock.recv(4)
        downloader_name_size = int.from_bytes(length_prefix, "big")

        downloader_name = self.sock.recv(downloader_name_size)
        downloader_name = downloader_name.decode()

        length_prefix = self.sock.recv(4)
        file_name_size = int.from_bytes(length_prefix, "big")

        file_name = self.sock.recv(file_name_size)
        file_name = file_name.decode()

        print(f"\n{downloader_name} downloaded your file named {file_name}!")


if __name__ == "__main__":
    my_client = Client()
    my_client.connect()
