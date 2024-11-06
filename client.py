import socket
import os

HOST = "127.0.0.1"
PORT = 9876

def file_transfer():
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
        print(f"Error: {e}")
        return None

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))

    while True:
        try:
            file, file_name, file_size, file_name_size = file_transfer()

            length_prefix = file_name_size.to_bytes(4, "big")
            file_name = file_name.encode()
            file_name_packet =  length_prefix + file_name
            s.sendall(file_name_packet)

            file_size_len = len(str(file_size))
            length_prefix = file_size_len.to_bytes(4, "big")
            file_size_b = str(file_size).encode()
            file_size_packet = length_prefix + file_size_b
            s.sendall(file_size_packet)

            bytes_sent = 0
            while bytes_sent < file_size:
                data = file.read(4096)
                if not data:
                    break
                s.sendall(data)
                bytes_sent += len(data)
                print(f"Progress: {(bytes_sent/file_size)*100:.2f}%")
            
        except Exception as e:
            print(f"File problem: {e}")

        finally:
            file.close()
