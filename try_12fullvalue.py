
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import multiprocessing
import threading
import time
import os
import psutil
from datetime import datetime

class MasterSlaveGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Master-Slave Communication System with Core Affinity")
        self.root.geometry("820x650")

        if psutil.cpu_count() < 2:
            messagebox.showerror("Error", "This program needs at least 2 CPU cores.")
            root.quit()

        self.set_core_affinity(0)

        # Shared memory values for workload
        self.master_workload = multiprocessing.Value('i', 100000)
        self.slave_workload = multiprocessing.Value('i', 100000)

        self.master_to_slave_queue = multiprocessing.Queue()
        self.slave_to_master_queue = multiprocessing.Queue()

        self.running = True
        self.communication_active = False
        self.communication_count = 0
        self.start_time = None

        self.setup_ui()
        self.start_cpu_monitor()
        self.root.after(100, self.poll_queues)

    def set_core_affinity(self, core):
        try:
            psutil.Process(os.getpid()).cpu_affinity([core])
        except Exception as e:
            print(f"Affinity error: {e}")

    def setup_ui(self):
        style = ttk.Style()
        style.configure("TLabel", font=('Helvetica', 10))
        style.configure("Header.TLabel", font=('Helvetica', 12, 'bold'))

        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Master-Slave Communication System", style="Header.TLabel").pack(anchor='center', pady=5)

        cpu_frame = ttk.LabelFrame(frame, text="CPU Usage", padding=10)
        cpu_frame.pack(fill=tk.X)

        self.core0_var = tk.StringVar()
        self.core1_var = tk.StringVar()

        self.core0_bar = ttk.Progressbar(cpu_frame, maximum=100)
        self.core0_bar.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(cpu_frame, textvariable=self.core0_var).pack()

        self.core1_bar = ttk.Progressbar(cpu_frame, maximum=100)
        self.core1_bar.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(cpu_frame, textvariable=self.core1_var).pack()

        sliders = ttk.LabelFrame(frame, text="Workload Adjustment", padding=10)
        sliders.pack(fill=tk.X, pady=10)

        self.master_slider = ttk.Scale(sliders, from_=10000, to=1500000, orient=tk.HORIZONTAL, command=self.update_master_workload)
        self.master_slider.set(self.master_workload.value)
        self.master_label = ttk.Label(sliders, text=f"Master: {self.master_workload.value}")
        self.master_label.pack(anchor='w')
        self.master_slider.pack(fill=tk.X)

        self.slave_slider = ttk.Scale(sliders, from_=10000, to=1500000, orient=tk.HORIZONTAL, command=self.update_slave_workload)
        self.slave_slider.set(self.slave_workload.value)
        self.slave_label = ttk.Label(sliders, text=f"Slave: {self.slave_workload.value}")
        self.slave_label.pack(anchor='w')
        self.slave_slider.pack(fill=tk.X)

        self.log = scrolledtext.ScrolledText(frame, height=15)
        self.log.pack(fill=tk.BOTH, expand=True, pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        self.start_btn = ttk.Button(btn_frame, text="Start", command=self.start_communication)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Exit", command=self.on_close).pack(side=tk.RIGHT, padx=5)

    def update_master_workload(self, val):
        val = int(float(val))
        with self.master_workload.get_lock():
            self.master_workload.value = val
        self.master_label.config(text=f"Master: {val}")

    def update_slave_workload(self, val):
        val = int(float(val))
        with self.slave_workload.get_lock():
            self.slave_workload.value = val
        self.slave_label.config(text=f"Slave: {val}")

    def start_cpu_monitor(self):
        def monitor():
            while self.running:
                usage = psutil.cpu_percent(percpu=True)
                if len(usage) >= 2:
                    self.root.after(0, self.update_cpu, usage)
                time.sleep(0.5)
        threading.Thread(target=monitor, daemon=True).start()

    def update_cpu(self, usage):
        self.core0_bar['value'] = usage[0]
        self.core0_var.set(f"Core 0 (Master): {usage[0]:.1f}%")
        self.core1_bar['value'] = usage[1]
        self.core1_var.set(f"Core 1 (Slave): {usage[1]:.1f}%")

    def start_communication(self):
        if self.communication_active:
            return

        self.communication_active = True
        self.communication_count = 0
        self.start_time = time.time()
        self.start_btn.config(state=tk.DISABLED)
        self.log_message("Starting communication for 60 seconds...")

        self.slave_proc = multiprocessing.Process(
            target=slave_process,
            args=(self.master_to_slave_queue, self.slave_to_master_queue, self.slave_workload)
        )
        self.slave_proc.start()

        threading.Thread(target=self.master_loop, daemon=True).start()

    def master_loop(self):
        try:
            psutil.Process(os.getpid()).cpu_affinity([0])
        except Exception:
            pass

        while self.communication_active:
            with self.master_workload.get_lock():
                iters = self.master_workload.value
            self.simulate_work(iters)

            msg = f"DATA_{self.communication_count}"
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.log_message(f"{timestamp} Master -> Slave: {msg}")
            self.master_to_slave_queue.put(msg)

            time.sleep(0.05)
            if time.time() - self.start_time >= 60:
                self.communication_active = False
                self.master_to_slave_queue.put("EXIT")
                self.root.after(0, self.on_comm_complete)

    def simulate_work(self, count):
        acc = 0
        for i in range(count):
            acc += (i % 7) * (i % 5)

    def poll_queues(self):
        while not self.slave_to_master_queue.empty():
            msg = self.slave_to_master_queue.get()
            self.communication_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.log_message(f"{timestamp} Slave -> Master: {msg}")
        if self.running:
            self.root.after(100, self.poll_queues)

    def on_comm_complete(self):
        self.log_message("Communication finished after 60 seconds.")
        self.start_btn.config(state=tk.NORMAL)

    def log_message(self, text):
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)

    def clear_log(self):
        self.log.delete(1.0, tk.END)

    def on_close(self):
        self.running = False
        self.communication_active = False
        if hasattr(self, 'slave_proc') and self.slave_proc.is_alive():
            self.master_to_slave_queue.put("EXIT")
            self.slave_proc.join(timeout=1)
            if self.slave_proc.is_alive():
                self.slave_proc.terminate()
        self.root.destroy()

def slave_process(master_to_slave_queue, slave_to_master_queue, workload):
    try:
        psutil.Process(os.getpid()).cpu_affinity([1])
    except Exception:
        pass

    while True:
        msg = master_to_slave_queue.get()
        if msg == "EXIT":
            break
        with workload.get_lock():
            iterations = workload.value
        acc = 0
        for i in range(iterations):
            acc += (i % 3) * (i % 11)
        slave_to_master_queue.put(f"ACK_{msg}")

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    root = tk.Tk()
    app = MasterSlaveGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
