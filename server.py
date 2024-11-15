import sys
import threading

from oop_server import Server
import tkinter as tk
from tkinter import filedialog, messagebox

if __name__ == "__main__":
    server = Server()

    # Function to handle connect button click
    def start_server():
        ip = ip_entry.get()
        port = port_entry.get()
        directory = dir_entry.get()

        if ip and port and directory:
            messagebox.showinfo("Server", f"Starting server at {ip}:{port}\nDirectory: {directory}")
            # Close the main window and open the console window
            root.withdraw()
            open_console_window()
            # Set file dir of server
            server.save_files_path = dir_entry.get()
            server_thread = threading.Thread(target=server.start, args=(), daemon=True)
            server_thread.start()
        else:
            messagebox.showwarning("Input Error", "Please fill in all fields.")

    # Function to open directory dialog
    def select_directory():
        directory = filedialog.askdirectory()
        if directory:
            dir_entry.delete(0, tk.END)
            dir_entry.insert(0, directory)

    def on_window_close():
        root.destroy()
        sys.exit(0)


    # Function to open a new console window
    def open_console_window():
        console_window = tk.Toplevel(root)
        console_window.title("Server Console")

        # Listbox to serve as the console log
        console_log = tk.Listbox(console_window, width=80, height=20)
        console_log.pack(padx=10, pady=10)

        # Bind the close event to the function
        console_window.protocol("WM_DELETE_WINDOW", on_window_close)

        # Button to simulate adding log messages to the console
        def add_log_message(message):
            console_log.insert(tk.END, message)
            console_log.yview(tk.END)  # Scroll to the latest message

        # Example log messages to demonstrate
        add_log_message("Server started...")
        add_log_message(f"Listening on IP {ip_entry.get()} and Port {port_entry.get()}")
        add_log_message("Ready to accept connections.")

        server.log_to_console = add_log_message


    # Create main window
    root = tk.Tk()
    root.title("Connection Interface")

    # IP Label and Entry
    tk.Label(root, text="IP Address:").grid(row=0, column=0, padx=10, pady=10)
    ip_entry = tk.Entry(root)
    ip_entry.grid(row=0, column=1, padx=10, pady=10)

    # Port Label and Entry
    tk.Label(root, text="Port:").grid(row=1, column=0, padx=10, pady=10)
    port_entry = tk.Entry(root)
    port_entry.grid(row=1, column=1, padx=10, pady=10)

    # Directory Label, Entry, and Button
    tk.Label(root, text="Directory:").grid(row=2, column=0, padx=10, pady=10)
    dir_entry = tk.Entry(root)
    dir_entry.grid(row=2, column=1, padx=10, pady=10)
    dir_button = tk.Button(root, text="Browse...", command=select_directory)
    dir_button.grid(row=2, column=2, padx=10, pady=10)

    # Connect Button
    start_button = tk.Button(root, text="Start", command=start_server)
    start_button.grid(row=3, column=0, columnspan=3, pady=20)


    # Run the application
    root.mainloop()
