
import socket
import os
import sys

DOWNLOAD = "1"
UPLOAD = "2"
LIST = "3"

HOST = "127.0.0.1"
PORT = 9876

class Client():

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
                print(f"Connection succesfully established")
            
            print(response)

            self.handle_command()

        except Exception as e:
            print(f"Error: {e}")

    def handle_command(self):
        while True:
            command = input("Do you want to download(1), upload(2) or list of files(3)?")
            if command == DOWNLOAD:
                self.sock.send("1".encode())
                self.file_download()
                # TODO: implement the download
            elif command == UPLOAD:
                print('merhaba')
                self.sock.send("2".encode())
                self.handle_connection()
            elif command == LIST:
                self.sock.send("3".encode())
                self.handle_get_file_list()
                pass
                # TODO implement getting the list 

    def handle_get_file_list(self):
        files_info_length_bytes = self.sock.recv(4)
        files_info_length = int.from_bytes(files_info_length_bytes,"big")

        files_info = self.sock.recv(files_info_length)
        files_info = files_info.decode()
        print(files_info)

    
    def handle_connection(self):
        try:
            file, file_name, file_size, file_name_size = self.file_transfer()

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
     

    def file_transfer(self):
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


            return (file, file_name, file_size, file_name_size)
        except Exception as e:
            print("merhaba")
            print(f"Error: {e}")
            return None

    def file_download(self):
        file_name = input("Please enter the file you want to download: ")
        file_name_size = len(file_name) 

        length_prefix = file_name_size.to_bytes(4, "big")
        file_name_b = file_name.encode()
        file_name_packet = length_prefix + file_name_b
        self.sock.sendall(file_name_packet)

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
    
if __name__ == "__main__":
    my_client = Client()
    my_client.connect()