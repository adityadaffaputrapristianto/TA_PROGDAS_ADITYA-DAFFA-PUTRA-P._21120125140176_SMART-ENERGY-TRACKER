"""
Smart Energy Usage Tracker - Interactive Real-Time GUI
Features:
- Perangkat dengan tombol ON/OFF per baris
- Timer berjalan real-time
- Undo, Remove, Export CSV
- UI Biru Modern (tanpa mengubah fitur)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time

# -----------------------
# Device & Manager1
# -----------------------
class Device:
    def __init__(self, name, watt):
        self.name = name
        self.watt = float(watt)
        self.start_time = None
        self.total_seconds = 0.0
        self.status = "OFF"

    def toggle(self):
        if self.status == "OFF":
            self.start()
        else:
            self.stop()

    def start(self):
        if self.start_time is None:
            self.start_time = time.time()
            self.status = "ON"

    def stop(self):
        if self.start_time is not None:
            self.total_seconds += time.time() - self.start_time
            self.start_time = None
            self.status = "OFF"

    def running_seconds(self):
        s = self.total_seconds
        if self.start_time is not None:
            s += time.time() - self.start_time
        return s

    def energy_wh(self):
        hours = self.running_seconds() / 3600.0
        return self.watt * hours


class ElectricityManager:
    def __init__(self):
        self.devices = []
        self.undo_stack = []

    def add_device(self, device):
        self.devices.append(device)
        self.undo_stack.append(("add", device))

    def remove_device(self, device):
        if device in self.devices:
            self.devices.remove(device)
            self.undo_stack.append(("remove", device))
            return True
        return False

    def undo(self):
        if not self.undo_stack:
            return False
        action, device = self.undo_stack.pop()
        if action == "add" and device in self.devices:
            self.devices.remove(device)
        elif action == "remove":
            self.devices.append(device)
        return True

    def total_wh(self):
        return sum(d.energy_wh() for d in self.devices)

    def estimate_cost(self, tarif_per_kwh=1500):
        kwh = self.total_wh() / 1000.0
        return kwh * tarif_per_kwh


# -----------------------
# GUI Row per Device
# -----------------------
class DeviceRow:
    def __init__(self, parent, device, update_callback, remove_callback):
        self.device = device
        self.update_callback = update_callback
        self.remove_callback = remove_callback

        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="x", pady=3)

        ttk.Style().configure("DeviceLabel.TLabel", background="#e8f0fe", font=("Segoe UI", 10))

        self.name_label = ttk.Label(self.frame, text=device.name, width=20, style="DeviceLabel.TLabel")
        self.name_label.pack(side="left", padx=5)

        self.watt_label = ttk.Label(self.frame, text=f"{device.watt} W", width=10, style="DeviceLabel.TLabel")
        self.watt_label.pack(side="left", padx=5)

        self.status_label = ttk.Label(self.frame, text=device.status, width=6, style="DeviceLabel.TLabel")
        self.status_label.pack(side="left", padx=5)

        self.timer_label = ttk.Label(self.frame, text="00:00", width=8, style="DeviceLabel.TLabel")
        self.timer_label.pack(side="left", padx=5)

        self.toggle_btn = ttk.Button(self.frame, text="Toggle", command=self.toggle)
        self.toggle_btn.pack(side="left", padx=5)

        self.remove_btn = ttk.Button(self.frame, text="Hapus", command=self.remove)
        self.remove_btn.pack(side="left", padx=5)

    def toggle(self):
        self.device.toggle()
        self.update_callback()

    def remove(self):
        if messagebox.askyesno("Konfirmasi", f"Hapus perangkat {self.device.name}?"):
            self.device.stop()
            self.frame.destroy()
            self.remove_callback(self.device)

    def update_display(self):
        # warna status
        if self.device.status == "ON":
            color = "#008000"  # hijau
        else:
            color = "#b00020"  # merah

        self.status_label.config(text=self.device.status, foreground=color)

        # update timer
        total_sec = int(self.device.running_seconds())
        mins = total_sec // 60
        secs = total_sec % 60
        self.timer_label.config(text=f"{mins:02d}:{secs:02d}")


# -----------------------
# Main App (UI Blue Theme)
# -----------------------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Energy Usage Tracker")
        self.root.geometry("650x500")
        self.manager = ElectricityManager()
        self.device_rows = []

        # ---------------------------------
        # 🎨 THEME BIRU MODERN
        # ---------------------------------
        style = ttk.Style()
        style.theme_use("default")

        root.configure(bg="#e8f0fe")

        style.configure("TFrame", background="#e8f0fe")
        style.configure("TLabel", background="#e8f0fe", foreground="#003366", font=("Segoe UI", 10))
        style.configure("TButton",
                        background="#1a73e8",
                        foreground="white",
                        padding=6,
                        font=("Segoe UI", 9, "bold"))
        style.map("TButton",
                  background=[("active", "#1558b0")])

        style.configure("TEntry", padding=4)

        # ---------------------------------
        # TOP FRAME
        # ---------------------------------
        top_frame = ttk.Frame(root, padding=10)
        top_frame.pack(fill="x")

        ttk.Label(top_frame, text="Nama:").pack(side="left")
        self.name_var = tk.StringVar()
        ttk.Entry(top_frame, textvariable=self.name_var, width=20).pack(side="left", padx=5)

        ttk.Label(top_frame, text="Daya (Watt):").pack(side="left")
        self.watt_var = tk.StringVar()
        ttk.Entry(top_frame, textvariable=self.watt_var, width=10).pack(side="left", padx=5)

        ttk.Button(top_frame, text="Tambah", command=self.add_device).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Undo", command=self.undo).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Export CSV", command=self.export_csv).pack(side="left", padx=5)

        # ---------------------------------
        # LIST FRAME
        # ---------------------------------
        self.list_frame = ttk.Frame(root, padding=10)
        self.list_frame.pack(fill="both", expand=True)

        # ---------------------------------
        # BOTTOM SUMMARY
        # ---------------------------------
        bottom_frame = ttk.Frame(root, padding=10)
        bottom_frame.pack(fill="x")

        self.total_wh_var = tk.StringVar(value="Total Energi: 0 Wh")
        self.cost_var = tk.StringVar(value="Estimasi Biaya: Rp 0")

        ttk.Label(bottom_frame, textvariable=self.total_wh_var).pack(side="left", padx=5)
        ttk.Label(bottom_frame, textvariable=self.cost_var).pack(side="left", padx=20)

        ttk.Label(bottom_frame, text="Tarif Rp/kWh:").pack(side="left")
        self.tarif_var = tk.StringVar(value="1500")
        ttk.Entry(bottom_frame, textvariable=self.tarif_var, width=10).pack(side="left", padx=5)

        # ---------------------------------
        # LOOP UPDATE
        # ---------------------------------
        self.update_loop()

    # -----------------------
    # Add / Undo / Remove
    # -----------------------
    def add_device(self):
        name = self.name_var.get().strip()
        watt_s = self.watt_var.get().strip()
        if not name or not watt_s:
            messagebox.showwarning("Input Tidak Lengkap", "Isi nama dan daya perangkat!")
            return
        try:
            watt = float(watt_s)
            if watt <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Format Salah", "Daya harus angka positif")
            return

        device = Device(name, watt)
        self.manager.add_device(device)

        row = DeviceRow(self.list_frame, device, self.update_summary, self.remove_device)
        self.device_rows.append(row)

        self.name_var.set("")
        self.watt_var.set("")

        self.update_summary()

    def undo(self):
        if not self.manager.undo():
            messagebox.showinfo("Undo", "Tidak ada aksi untuk di-undo.")
            return

        for row in self.device_rows:
            row.frame.destroy()

        self.device_rows = []
        for device in self.manager.devices:
            row = DeviceRow(self.list_frame, device, self.update_summary, self.remove_device)
            self.device_rows.append(row)

        self.update_summary()

    def remove_device(self, device):
        self.manager.remove_device(device)
        self.device_rows = [row for row in self.device_rows if row.device != device]
        self.update_summary()

    # -----------------------
    # Update Display
    # -----------------------
    def update_summary(self):
        for row in self.device_rows:
            row.update_display()
        total_wh = self.manager.total_wh()
        try:
            tarif = float(self.tarif_var.get())
        except:
            tarif = 1500
        cost = self.manager.estimate_cost(tarif)
        self.total_wh_var.set(f"Total Energi: {total_wh:.2f} Wh")
        self.cost_var.set(f"Estimasi Biaya: Rp {int(cost):,}".replace(",", "."))

    def update_loop(self):
        self.update_summary()
        self.root.after(1000, self.update_loop)

    # -----------------------
    # Export CSV
    # -----------------------
    def export_csv(self):
        fname = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
        if not fname:
            return
        try:
            import csv
            with open(fname, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Nama Perangkat","Daya (W)","Status","Waktu (s)","Energi (Wh)"])
                for device in self.manager.devices:
                    writer.writerow([
                        device.name, device.watt, device.status,
                        int(device.running_seconds()), f"{device.energy_wh():.4f}"
                    ])
            messagebox.showinfo("Export Berhasil", f"Laporan tersimpan: {fname}")
        except Exception as e:
            messagebox.showerror("Export Gagal", str(e))


# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
