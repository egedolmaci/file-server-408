import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from server_backend import Server

'''
This file contains the GUI implementation of the server.
'''


class ServerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.console_log = None
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
        self.dir_label = tk.Label(self, text="Directory:")
        self.dir_label.grid(row=2, column=0, padx=10, pady=10)
        self.dir_entry = tk.Entry(self)
        self.dir_entry.grid(row=2, column=1, padx=10, pady=10)
        self.dir_button = tk.Button(self, text="Browse...", command=self.select_directory)
        self.dir_button.grid(row=2, column=2, padx=10, pady=10)

        # Connect Button
        self.start_button = tk.Button(self, text="Start", command=self.start_server)
        self.start_button.grid(row=3, column=0, columnspan=3, pady=20)
        self.resizable(width=False, height=False)

        # Create server object
        self.server = Server()

    def start_server(self):
        ip = self.ip_entry.get()
        port = self.port_entry.get()
        directory = self.dir_entry.get()

        if ip and port and directory:
            messagebox.showinfo("Server", f"Starting server at {ip}:{port}\nDirectory: {directory}")
            self.withdraw()
            self.open_console_window()

            # Set path, ip, port of the server
            self.server.save_files_path = directory
            self.server.host = self.ip_entry.get()
            self.server.port = int(self.port_entry.get())

            # Start the server thread
            server_thread = threading.Thread(target=self.server.start, args=(), daemon=True)
            server_thread.start()
        else:
            messagebox.showwarning("Input Error", "Please fill in all fields.")

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)

    def on_window_close(self):
        self.destroy()
        sys.exit(0)

    def open_console_window(self):
        self.resizable(width=True, height=True)
        console_window = tk.Toplevel(self)
        console_window.title("Server Console")
        console_window.rowconfigure(0, weight=1)
        console_window.columnconfigure(0, weight=1)

        # Listbox to serve as the console log
        self.console_log = tk.Listbox(console_window, width=80, height=20)
        self.console_log.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Bind the close event to the function
        console_window.protocol("WM_DELETE_WINDOW", self.on_window_close)

        def add_log_message(message):
            self.console_log.insert(tk.END, message)
            self.console_log.yview(tk.END)

        # Initial logs
        add_log_message("Server started...")
        add_log_message(f"Listening on IP {self.ip_entry.get()} and Port {self.port_entry.get()}")
        add_log_message("Ready to accept connections.")

        self.server.log_to_console = add_log_message


if __name__ == "__main__":
    app = ServerGUI()
    app.mainloop()
