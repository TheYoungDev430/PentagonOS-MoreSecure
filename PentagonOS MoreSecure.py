mport tkinter as tk
from tkinter import messagebox, Menu, Toplevel, Label, Button, Entry, scrolledtext, filedialog, Listbox, Scrollbar, Text, END
import subprocess
import os
import platform
import psutil
import winsound
import configparser
from time import strftime

CONFIG_FILE = "skeepos_config.ini"

def load_password():
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        config['Settings'] = {'password': '4'}
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
    else:
        config.read(CONFIG_FILE)
    return config['Settings'].get('password', '4')

def save_password(new_password):
    config = configparser.ConfigParser()
    config['Settings'] = {'password': new_password}
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

class TerminalApp(Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("skeepOS Terminal")
        self.geometry("600x400")

        self.output = scrolledtext.ScrolledText(self, wrap=tk.WORD, state='disabled')
        self.output.pack(expand=True, fill='both')

        self.input = Entry(self)
        self.input.pack(fill='x')
        self.input.bind("<Return>", self.execute_command)

    def write_output(self, text):
        self.output.configure(state='normal')
        self.output.insert(tk.END, text + "\n")
        self.output.configure(state='disabled')
        self.output.see(tk.END)

    def execute_command(self, event=None):
        command = self.input.get().strip()
        self.write_output(f"> {command}")
        self.input.delete(0, tk.END)

        if command.startswith("echo "):
            self.write_output(command[5:])
        elif command == "cpuinfo":
            info = f"Processor: {platform.processor()}\nCores: {psutil.cpu_count(logical=False)}\nThreads: {psutil.cpu_count(logical=True)}"
            self.write_output(info)
        elif command.startswith("open "):
            app_name = command[5:].strip().lower()
            apps = {
                "notepad": "notepad.exe",
                "paint": "mspaint.exe",
                "cmd": "cmd.exe",
                "calculator": "calc.exe",
                "registry": "regedit.exe",
                "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            }
            if app_name in apps:
                try:
                    subprocess.Popen([apps[app_name]])
                except Exception as e:
                    self.write_output(f"Failed to open {app_name}: {e}")
            else:
                self.write_output(f"Unknown app: {app_name}. Try one of: {', '.join(apps.keys())}")
        elif command == "help":
            help_text = (
                "Available commands:\n"
                "  echo <text>         - Print text\n"
                "  cpuinfo             - Show CPU information\n"
                "  open <app>          - Launch app (notepad, paint, cmd, calculator, registry, edge)\n"
                "  clear               - Clear terminal output\n"
                "  exit                - Close terminal\n"
                "  help                - Show this help message"
            )
            self.write_output(help_text)
        elif command == "clear":
            self.output.configure(state='normal')
            self.output.delete(1.0, tk.END)
            self.output.configure(state='disabled')
        elif command == "exit":
            self.destroy()
        else:
            self.write_output("Unknown command. Try: echo, cpuinfo, open <app>, clear, exit, help")

class FileManager(Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("File Manager")
        self.geometry("600x400")

        self.dir_label = Label(self, text="Current Directory:")
        self.dir_label.pack()

        self.file_listbox = Listbox(self, width=80)
        self.file_listbox.pack(side="left", fill="both", expand=True)
        self.file_listbox.bind("<Double-Button-1>", self.open_selected)

        scrollbar = Scrollbar(self)
        scrollbar.pack(side="right", fill="y")
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.file_listbox.yview)

        self.file_content = Text(self, wrap="word", height=10)
        self.file_content.pack(fill="both", expand=True)

        Button(self, text="Browse Directory", command=self.browse_directory).pack(pady=5)

        self.current_dir = os.getcwd()
        self.update_file_list()

    def browse_directory(self):
        selected_dir = filedialog.askdirectory(initialdir=self.current_dir)
        if selected_dir:
            self.current_dir = selected_dir
            self.update_file_list()

    def update_file_list(self):
        self.file_listbox.delete(0, END)
        self.dir_label.config(text=f"Current Directory: {self.current_dir}")
        try:
            for item in os.listdir(self.current_dir):
                self.file_listbox.insert(END, item)
        except Exception as e:
            self.file_listbox.insert(END, f"Error reading directory: {e}")

    def open_selected(self, event):
        selected = self.file_listbox.get(self.file_listbox.curselection())
        path = os.path.join(self.current_dir, selected)
        if os.path.isdir(path):
            self.current_dir = path
            self.update_file_list()
        else:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.file_content.delete(1.0, END)
                self.file_content.insert(END, content)
            except Exception as e:
                self.file_content.delete(1.0, END)
                self.file_content.insert(END, f"Error opening file: {e}")

class SettingsPanel(Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Settings")
        self.geometry("300x150")

        Label(self, text="Change Password:", font=("Arial", 12)).pack(pady=10)
        self.new_password_entry = Entry(self, show="*", font=("Arial", 14))
        self.new_password_entry.pack(pady=5)
        Button(self, text="Save", command=self.save_password).pack(pady=10)

    def save_password(self):
        new_password = self.new_password_entry.get()
        if new_password:
            save_password(new_password)
            messagebox.showinfo("Success", "Password changed successfully!")
            self.destroy()
        else:
            messagebox.showerror("Error", "Password cannot be empty.")

class StartMenuSearchPanel(Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Search Files")
        self.geometry("500x400")

        Label(self, text="Search Files in Home Directory:", font=("Arial", 12)).pack(pady=5)
        self.search_entry = Entry(self, width=50)
        self.search_entry.pack(pady=5)
        self.search_entry.bind("<Return>", self.perform_search)

        self.result_listbox = Listbox(self, width=70)
        self.result_listbox.pack(side="left", fill="both", expand=True)
        self.result_listbox.bind("<Double-Button-1>", self.open_selected_file)

        scrollbar = Scrollbar(self)
        scrollbar.pack(side="right", fill="y")
        self.result_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.result_listbox.yview)

        self.file_content = Text(self, wrap="word", height=10)
        self.file_content.pack(fill="both", expand=True)

        self.search_dir = os.path.expanduser("~")

    def perform_search(self, event=None):
        query = self.search_entry.get().lower()
        self.result_listbox.delete(0, END)
        for root, dirs, files in os.walk(self.search_dir):
            for name in files:
                if query in name.lower():
                    full_path = os.path.join(root, name)
                    self.result_listbox.insert(END, full_path)

    def open_selected_file(self, event=None):
        selected = self.result_listbox.get(self.result_listbox.curselection())
        try:
            if os.access(selected, os.X_OK):
                os.startfile(selected)
            else:
                with open(selected, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.file_content.delete(1.0, END)
                self.file_content.insert(END, content)
        except Exception as e:
            self.file_content.delete(1.0, END)
            self.file_content.insert(END, f"Error opening file: {e}")

class SkeepOS:
    def __init__(self, root):
        self.root = root
        self.root.title("skeepOS Simulator")
        self.root.geometry("800x600")
        self.root.configure(bg="black")
        winsound.PlaySound(r"C:\Windows\Media\Ring01.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
        self.password = load_password()
        self.show_login_screen()

    def show_login_screen(self):
        self.clear_window()
        self.login_frame = tk.Frame(self.root, bg="black")
        self.login_frame.pack(expand=True)

        self.time_label = tk.Label(self.login_frame, text="", fg="white", bg="black", font=("Arial", 24))
        self.time_label.pack(pady=20)
        self.update_time()

        self.root.bind("<Key>", self.show_password_entry)

    def update_time(self):
        self.time_label.config(text=strftime("%I:%M:%S %p\n%d-%b-%Y"))
        self.root.after(1000, self.update_time)

    def show_password_entry(self, event=None):
        self.root.unbind("<Key>")
        for widget in self.login_frame.winfo_children():
            widget.destroy()

        tk.Label(self.login_frame, text="Enter Password:", fg="white", bg="black", font=("Arial", 16)).pack(pady=10)
        self.password_entry = tk.Entry(self.login_frame, show="*", font=("Arial", 18))
        self.password_entry.pack(pady=10)
        tk.Button(self.login_frame, text="Login", font=("Arial", 14), command=self.check_password).pack(pady=10)

    def check_password(self):
        if self.password_entry.get() == self.password:
            self.show_desktop()
        else:
            messagebox.showerror("Error", "Incorrect Password")

    def show_desktop(self):
        self.clear_window()
        self.root.configure(bg="lightblue")

        self.desktop_frame = tk.Frame(self.root, bg="lightblue")
        self.desktop_frame.pack(expand=True, fill="both")

        self.taskbar = tk.Frame(self.root, bg="gray", height=30)
        self.taskbar.pack(side="bottom", fill="x")

        self.start_button = tk.Button(self.taskbar, text="Start", command=self.show_start_menu)
        self.start_button.pack(side="left", padx=5)

        self.clock_label = tk.Label(self.taskbar, text="", bg="gray", fg="white")
        self.clock_label.pack(side="right", padx=10)
        self.update_clock()

        self.create_desktop_icons()

    def update_clock(self):
        self.clock_label.config(text=strftime("%I:%M:%S %p | %d-%b-%Y"))
        self.root.after(1000, self.update_clock)

    def show_start_menu(self):
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="Notepad", command=lambda: subprocess.Popen(["notepad.exe"]))
        menu.add_command(label="Paint", command=lambda: subprocess.Popen(["mspaint.exe"]))
        menu.add_command(label="CMD", command=lambda: subprocess.Popen(["cmd.exe"]))
        menu.add_command(label="Registry Editor", command=lambda: subprocess.Popen(["regedit.exe"]))
        menu.add_command(label="Microsoft Edge", command=self.open_edge)
        menu.add_command(label="Calculator", command=lambda: subprocess.Popen(["calc.exe"]))
        menu.add_command(label="File Explorer", command=self.open_file_explorer)
        menu.add_command(label="Wallpapers", command=self.open_wallpaper_app)
        menu.add_command(label="Terminal", command=self.open_terminal)
        menu.add_command(label="Settings", command=self.open_settings_panel)
        menu.add_command(label="Search Files", command=lambda: StartMenuSearchPanel(self.root))
        menu.add_command(label="Shutdown", command=self.shutdown_os)
        menu.post(self.start_button.winfo_rootx(), self.start_button.winfo_rooty() - menu.winfo_reqheight())

    def create_desktop_icons(self):
        apps = [
            ("Notepad", lambda: subprocess.Popen(["notepad.exe"]), "Notepad for skeepOS", 50, 50),
            ("Paint", lambda: subprocess.Popen(["mspaint.exe"]), "Paint for skeepOS", 150, 50),
            ("CMD", lambda: subprocess.Popen(["cmd.exe"]), "Command Prompt for skeepOS", 250, 50),
            ("Registry", lambda: subprocess.Popen(["regedit.exe"]), "Registry Editor for skeepOS", 350, 50),
            ("Edge", self.open_edge, "Edge browser for skeepOS", 450, 50),
            ("Calculator", lambda: subprocess.Popen(["calc.exe"]), "Calculator for skeepOS", 550, 50),
            ("Terminal", self.open_terminal, "Terminal for skeepOS", 650, 50),
            ("Search", lambda: StartMenuSearchPanel(self.root), "Search files in home directory", 50, 150),
            ("Settings", self.open_settings_panel, "Change system settings", 150, 150),
            ("FileMgr", self.open_file_explorer, "File Manager for skeepOS", 250, 150)
        ]
        for label, func, desc, x, y in apps:
            icon = tk.Button(self.desktop_frame, text=label, width=10, height=2, command=func)
            icon.place(x=x, y=y)
            icon.bind("<Button-3>", lambda e, f=func, d=desc, l=label: self.show_icon_menu(e, f, d, l))

    def show_icon_menu(self, event, func, desc, label):
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label=f"Open {label}", command=func)
        menu.add_command(label="Properties", command=lambda: messagebox.showinfo("Properties", desc))
        menu.post(event.x_root, event.y_root)

    def open_edge(self):
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
        for path in edge_paths:
            if os.path.exists(path):
                subprocess.Popen([path])
                return
        messagebox.showerror("Error", "Edge not found!")

    def open_file_explorer(self):
        FileManager(self.root)

    def open_wallpaper_app(self):
        wallpaper_window = Toplevel(self.root)
        wallpaper_window.title("Wallpapers")
        wallpaper_window.geometry("300x150")
        Label(wallpaper_window, text="Choose Wallpaper:", font=("Aparajita", 14)).pack(pady=10)
        Button(wallpaper_window, text="Default", command=lambda: self.set_wallpaper("lightblue")).pack(pady=5)
        Button(wallpaper_window, text="Teal", command=lambda: self.set_wallpaper("teal")).pack(pady=5)

    def set_wallpaper(self, color):
        self.root.configure(bg=color)
        self.desktop_frame.configure(bg=color)

    def open_terminal(self):
        TerminalApp(self.root)

    def open_settings_panel(self):
        SettingsPanel(self.root)

    def shutdown_os(self):
        self.clear_window()
        self.root.configure(bg="black")
        Label(self.root, text="Exiting safely...", fg="white", bg="black", font=("Arial", 24)).pack(expand=True)
        winsound.PlaySound(r"C:\Windows\Media\Alarm01.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
        self.root.after(2000, self.root.quit)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SkeepOS(root)
    root.mainloop()
