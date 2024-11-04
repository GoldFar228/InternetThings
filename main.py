import tkinter as tk
import time
import threading


class IoTDevice:
    def __init__(self):
        self.moisture_level = 100  # Начальный уровень влажности
        self.manual_mode = True  # Режим по умолчанию - ручной
        self.pump_on = False

    def update_moisture(self):
        if self.pump_on:
            self.moisture_level += 10
            if self.moisture_level > 100:
                self.moisture_level = 100
        else:
            self.moisture_level -= 5
            if self.moisture_level < 0:
                self.moisture_level = 0

    def toggle_pump(self):
        self.pump_on = not self.pump_on

    def set_manual_mode(self):
        self.manual_mode = True

    def set_auto_mode(self):
        self.manual_mode = False

    def auto_check(self):
        if not self.manual_mode and self.moisture_level < 30:
            self.pump_on = True
        elif not self.manual_mode and self.moisture_level > 70:
            self.pump_on = False


class IoTApp:
    def __init__(self, root, device):
        self.device = device
        self.root = root
        self.root.title("IoT Device Simulator")

        self.moisture_label = tk.Label(root, text="Moisture Level: ")
        self.moisture_label.pack()

        self.moisture_value = tk.Label(root, text=f"{self.device.moisture_level}%")
        self.moisture_value.pack()

        self.pump_button = tk.Button(root, text="Toggle Pump", command=self.toggle_pump)
        self.pump_button.pack()

        self.mode_button = tk.Button(root, text="Set to Auto Mode", command=self.toggle_mode)
        self.mode_button.pack()

        self.status_label = tk.Label(root, text="Mode: Manual")
        self.status_label.pack()

        self.update_data()

    def toggle_pump(self):
        if self.device.manual_mode:
            self.device.toggle_pump()

    def toggle_mode(self):
        if self.device.manual_mode:
            self.device.set_auto_mode()
            self.status_label.config(text="Mode: Automatic")
            self.mode_button.config(text="Set to Manual Mode")
        else:
            self.device.set_manual_mode()
            self.status_label.config(text="Mode: Manual")
            self.mode_button.config(text="Set to Auto Mode")

    def update_data(self):
        self.device.update_moisture()
        self.device.auto_check()
        self.moisture_value.config(text=f"{self.device.moisture_level}%")

        if self.device.pump_on:
            self.pump_button.config(bg="green", text="Pump ON")
        else:
            self.pump_button.config(bg="red", text="Pump OFF")

        # Обновление данных раз в 10 секунд
        self.root.after(10000, self.update_data)


# Запуск программы
root = tk.Tk()
device = IoTDevice()
app = IoTApp(root, device)
root.mainloop()
