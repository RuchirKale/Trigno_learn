import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageTk, ImageFilter
import serial
import serial.tools.list_ports
import threading
import math
import time

BAUDRATE = 9600


class TrigVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Arduino Trigonometry Visualizer")
        self.root.geometry("750x650")
        self.root.configure(bg="#0d0d0d")
        self.running = False
        self.arduino = None

        # --- Title ---
        tk.Label(root, text="Trigno_Learn",
                 font=("Segoe UI", 18, "bold"),
                 bg="#0d0d0d", fg="#00ffcc").pack(pady=10)

        # --- Status ---
        self.status = tk.Label(root, text="Status: Disconnected",
                               bg="#0d0d0d", fg="red", font=("Consolas", 12))
        self.status.pack()

        # --- Buttons ---
        btn_frame = tk.Frame(root, bg="#0d0d0d")
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Connect Arduino", command=self.connect_arduino,
                  bg="#2a2a2a", fg="white", font=("Arial", 11),
                  relief="flat", activebackground="#00ffcc").grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Disconnect", command=self.disconnect_arduino,
                  bg="#3a3a3a", fg="white", font=("Arial", 11),
                  relief="flat", activebackground="#ff6666").grid(row=0, column=1, padx=5)

        # --- Angle Display ---
        self.angle_label = tk.Label(root, text="Angle: --°",
                                    font=("Consolas", 22, "bold"),
                                    bg="#0d0d0d", fg="#00ff9d")
        self.angle_label.pack(pady=10)

        # --- Measurements ---
        self.data_label = tk.Label(root, text="Base: -- cm   Height: -- cm   Hypo: -- cm",
                                   font=("Consolas", 14), bg="#0d0d0d", fg="#dddddd")
        self.data_label.pack(pady=5)

        # --- Trig Values ---
        self.trig_label = tk.Label(root, text="sin: --   cos: --   tan: --",
                                   font=("Consolas", 14), bg="#0d0d0d", fg="#ffffff")
        self.trig_label.pack(pady=5)

        # --- Frosted Glass Panel with Blurred Borders ---
        self.panel_width, self.panel_height = 420, 420
        self.panel_canvas = tk.Canvas(
            root, width=self.panel_width, height=self.panel_height, bg="#0d0d0d", highlightthickness=0)
        self.panel_canvas.pack(pady=15)

        frosted_img = self.create_frosted_panel(
            self.panel_width, self.panel_height, radius=40, blur=6)
        self.panel_canvas.image = frosted_img
        self.panel_canvas.create_image(0, 0, image=frosted_img, anchor="nw")

        # --- Matplotlib Figure ---
        self.fig, self.ax = plt.subplots(figsize=(4, 4))
        self.ax.set_facecolor("none")  # transparent so frosted panel shows
        self.ax.set_xlim(-0.2, 1.2)
        self.ax.set_ylim(-0.2, 1.2)
        self.ax.axis("off")
        self.triangle, = self.ax.plot(
            [], [], 'o-', color="#00bfff", linewidth=2)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.panel_canvas)
        self.canvas.get_tk_widget().place(x=10, y=10, width=400, height=400)

        # --- Footer ---
        tk.Label(root, text="📡 Connected to Arduino • Live Trigonometric Simulation",
                 bg="#0d0d0d", fg="#888", font=("Arial", 10)).pack(side="bottom", pady=8)

    # --- Create frosted panel with blurred borders ---
    def create_frosted_panel(self, width, height, radius=40, blur=6):
        # semi-transparent white
        base = Image.new("RGBA", (width, height), (255, 255, 255, 180))
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)
        rounded = Image.new("RGBA", (width, height))
        rounded.paste(base, (0, 0), mask=mask)
        blurred = rounded.filter(ImageFilter.GaussianBlur(blur))
        return ImageTk.PhotoImage(blurred)

    # --- Port Finder ---
    def find_arduino_port(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "Arduino" in port.description or "CH340" in port.description:
                return port.device
        return None

    # --- Connect ---
    def connect_arduino(self):
        port = self.find_arduino_port()
        if not port:
            messagebox.showerror("404", "❌ 404: Arduino not found.")
            self.status.config(text="Status: Not Found", fg="red")
            return
        try:
            self.arduino = serial.Serial(port, BAUDRATE, timeout=1)
            time.sleep(2)
            self.running = True
            self.status.config(text=f"Connected: {port}", fg="lime")
            threading.Thread(target=self.read_serial, daemon=True).start()
        except serial.SerialException:
            messagebox.showerror("Error", "Failed to connect.")
            self.status.config(text="Status: Error", fg="red")

    # --- Disconnect ---
    def disconnect_arduino(self):
        self.running = False
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
        self.status.config(text="Status: Disconnected", fg="red")

    # --- Read Serial ---
    def read_serial(self):
        while self.running:
            try:
                if self.arduino.in_waiting > 0:
                    line = self.arduino.readline().decode('utf-8', errors='ignore').strip()
                    if line.startswith("Base (Adj.):"):
                        base = float(line.split(":")[1].split()[0])
                        hypo = float(self.arduino.readline(
                        ).decode().split(":")[1].split()[0])
                        height = float(self.arduino.readline(
                        ).decode().split(":")[1].split()[0])
                        angle = float(self.arduino.readline(
                        ).decode().split(":")[1].split()[0])
                        sin_val = float(
                            self.arduino.readline().decode().split(":")[1])
                        cos_val = float(
                            self.arduino.readline().decode().split(":")[1])
                        tan_line = self.arduino.readline().decode().strip()
                        tan_val = tan_line.split(":")[1].strip()
                        if tan_val == "∞":
                            tan_val = float('inf')
                        else:
                            tan_val = float(tan_val)
                        self.update_display(
                            base, height, hypo, angle, sin_val, cos_val, tan_val)
            except Exception as e:
                print(f"Serial error: {e}")
                break

    # --- Update UI ---
    def update_display(self, base, height, hypo, angle, sin_val, cos_val, tan_val):
        self.angle_label.config(text=f"Angle: {angle:.1f}°")
        self.data_label.config(
            text=f"Base: {base:.1f} cm   Height: {height:.1f} cm   Hypo: {hypo:.1f} cm")
        self.trig_label.config(
            text=f"sin: {sin_val:.3f}   cos: {cos_val:.3f}   tan: {'∞' if tan_val == float('inf') else f'{tan_val:.3f}'}")

        self.ax.cla()
        self.ax.set_xlim(-0.2, 1.2)
        self.ax.set_ylim(-0.2, 1.2)
        self.ax.axis("off")
        self.ax.set_facecolor("#181818")

        x = cos_val
        y = sin_val
        self.ax.plot([0, x, x, 0], [0, y, 0, 0], 'o-',
                     color="#00bfff", linewidth=2)
        self.ax.text(0.5, 0.5, f"{angle:.1f}°", color="white", fontsize=12)
        self.canvas.draw()


# --- Run App ---
if __name__ == "__main__":
    root = tk.Tk()
    app = TrigVisualizer(root)
    root.mainloop()
