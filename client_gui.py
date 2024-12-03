import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from client_backend import Client
from parser import *


class ClientGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.console_text = None
        self.delete_button = None
        self.download_button = None
        self.upload_button = None
        self.retrieve_button = None
        self.user_interface = None
        self.file_list = None
        self.client = None

        self.title("Connection Interface")

        # IP Label and Entry
        self.ip_label = tk.Label(self, text="IP Address:")
        self.ip_label.grid(row=0, column=0, padx=10, pady=10)
        self.ip_entry = tk.Entry(self)
        self.ip_entry.grid(row=0, column=1, padx=10, pady=10)

        # Port Label and Entry
        self.port_label = tk.Label(self, text="Port:")
        self.port_label.grid(row=1, column=0, padx=10, pady=10)
        self.port_entry = tk.Entry(self)
        self.port_entry.grid(row=1, column=1, padx=10, pady=10)

        # Directory Label, Entry, and Button
        self.dir_label = tk.Label(self, text="User Name:")
        self.dir_label.grid(row=2, column=0, padx=10, pady=10)
        self.user_name = tk.Entry(self)
        self.user_name.grid(row=2, column=1, padx=10, pady=10)

        # Connect Button
        self.connect_button = tk.Button(self, text="Connect", command=self.start_client)
        self.connect_button.grid(row=3, column=0, columnspan=3, pady=20)

        self.resizable(width=False, height=False)

    def start_client(self):

        ip = self.ip_entry.get()
        port = self.port_entry.get()
        user_name = self.user_name.get()

        self.client = Client()
        self.client.ui_update_callback = self.ui_update_callback

        if ip and port and user_name:
            messagebox.showinfo("Server", f"Connecting to {ip}:{port}\nWith name: {user_name}")
            self.withdraw()  # Hide the current window
            self.client.alias = user_name
            self.client.host = self.ip_entry.get()
            self.client.port = int(self.port_entry.get())
            server_thread = threading.Thread(target=self.client.connect, args=(), daemon=True)
            server_thread.start()
            self.client.open_client_user_interface = self.open_client_user_interface

        else:
            messagebox.showwarning("Input Error", "Please fill in all fields.")

    def open_client_user_interface(self):
        self.resizable(width=True, height=True)
        self.user_interface = tk.Toplevel(self)
        self.user_interface.title("File Server Client")
        self.user_interface.geometry("1400x600")  # Set the window size

        # Main grid configuration for the user interface window
        self.user_interface.grid_columnconfigure(0, weight=1)
        self.user_interface.grid_columnconfigure(1, weight=1)
        self.user_interface.grid_rowconfigure(1, weight=1)

        # File List (Treeview)
        self.file_list = ttk.Treeview(self.user_interface)
        self.file_list["columns"] = ("1")
        self.file_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.file_list.column("#0", width=200)
        self.file_list.column("1", width=200)
        self.file_list.heading("#0", text="Filename")
        self.file_list.heading("1", text="Owner")

        # Buttons
        button_frame = tk.Frame(self.user_interface)
        button_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.retrieve_button = tk.Button(button_frame, text="Retrieve Server Data", command=self.retrieve_server_data)
        self.retrieve_button.grid(row=0, column=0, padx=5)

        self.upload_button = tk.Button(button_frame, text="Upload File", command=self.upload_file)
        self.upload_button.grid(row=0, column=1, padx=5)

        self.download_button = tk.Button(button_frame, text="Download", command=self.download_file)
        self.download_button.grid(row=0, column=2, padx=5)

        self.delete_button = tk.Button(button_frame, text="Delete", command=self.delete_file)
        self.delete_button.grid(row=0, column=3, padx=5)

        # User Info
        user_info_frame = tk.Frame(self.user_interface)
        user_info_frame.grid(row=0, column=1, sticky="e", padx=10, pady=10)

        user_name_label = tk.Label(user_info_frame, text=f"User Name: {self.client.alias}")
        user_name_label.grid(row=0, column=0, pady=2, sticky="e")

        server_info_label = tk.Label(user_info_frame, text=f"Server Address: {self.client.host}:{self.client.port}")
        server_info_label.grid(row=1, column=0, pady=2, sticky="e")

        # Console Text Box
        self.console_text = tk.Text(self.user_interface, height=20, width=80)
        self.console_text.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        # Bind the close event to the function
        self.user_interface.protocol("WM_DELETE_WINDOW", self.on_window_close)

    def on_window_close(self):
        self.destroy()
        sys.exit(0)

    def retrieve_server_data(self):
        # Code to retrieve and display server file data
        self.log_message("Retrieving server data...")
        # Simulate data retrieval
        self.log_message("Server data retrieved successfully.")
        self.client.handle_command(LIST, None)

    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.log_message(f"Uploading file: {file_path}")
            # Code to upload the selected file to the server
            self.client.handle_command(UPLOAD, file_path)
            self.log_message("File uploaded successfully.")

    def download_file(self):
        selected_item = self.file_list.focus()
        if selected_item:
            self.log_message(f"Downloading file: {self.file_list.item(selected_item)['text']}")

            self.client.handle_command(DOWNLOAD, self.file_list.item(selected_item)['values'][0] + "_" +
                                       self.file_list.item(selected_item)['text'])
            # Code to download the selected file from the server
            self.log_message("File downloaded successfully.")

    def delete_file(self):
        selected_item = self.file_list.focus()
        if selected_item:
            self.log_message(f"Trying to delete file: {self.file_list.item(selected_item)['text']}")
            self.client.handle_command(DELETE, self.file_list.item(selected_item)['values'][0] + "_"
                                       + self.file_list.item(selected_item)['text'])
        else:
            self.log_message("Please select a file to delete!")

    def log_message(self, message):
        self.console_text.insert(tk.END, f"{message}\n")
        self.console_text.see(tk.END)

    def ui_update_callback(self, command, data):
        if command == LIST:
            self.file_list.delete(*self.file_list.get_children())
            for key in data.keys():
                for value in data[key]:
                    self.file_list.insert("", "end", text=value, values=(key,))

        if command == DELETE:
            if data:
                self.log_message("File deleted successfully.")
                self.client.send_get_file_list_request()
            else:
                self.log_message("File could not be deleted you don't own this file!")

        if command == "LOG":
            self.log_message(data)

        if command == "ERROR":
            if data == "USERNAME_TAKEN":
                messagebox.showwarning("Error", "This user is already connected!")
                self.destroy()
                sys.exit(0)

            if data == "CONNECTION_LOST":
                messagebox.showwarning("Error", "Server connection has been lost!")
                self.destroy()
                sys.exit(0)

            if data == "CONNECTION_ERROR":
                messagebox.showwarning("Error", "Could not connect to the server!")
                self.destroy()
                sys.exit(0)


if __name__ == "__main__":
    app = ClientGUI()
    app.mainloop()
