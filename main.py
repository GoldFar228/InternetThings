import tkinter as tk
import time
import threading
import paho.mqtt.client as mqtt

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

class MQTTHandler:
    def __init__(self, device):
        self.device = device
        self.client = mqtt.Client(protocol=mqtt.MQTTv5)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # Подключение к открытому MQTT-серверу
        self.client.connect("test.mosquitto.org", 1883, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc, properties=None):
        print("Connected to MQTT server with result code " + str(rc))
        # Подписка на каналы управления
        self.client.subscribe("iot/device/control")
        self.client.subscribe("iot/device/mode")

    def on_message(self, client, userdata, msg):
        print(f"Received message '{msg.payload.decode()}' on topic '{msg.topic}'")
        if msg.topic == "iot/device/control":
            if msg.payload.decode() == "toggle_pump":
                print("Toggling pump based on received command.")
                self.device.toggle_pump()
        elif msg.topic == "iot/device/mode":
            if msg.payload.decode() == "manual":
                self.device.set_manual_mode()
            elif msg.payload.decode() == "auto":
                self.device.set_auto_mode()

    def publish_data(self):
        # Публикация данных на MQTT-сервер
        self.client.publish("iot/device/moisture", str(self.device.moisture_level))

class IoTApp:
    def __init__(self, root, device, mqtt_handler):
        self.device = device
        self.mqtt_handler = mqtt_handler
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
            self.mqtt_handler.client.publish("iot/device/control", "toggle_pump")

    def toggle_mode(self):
        if self.device.manual_mode:
            self.device.set_auto_mode()
            self.status_label.config(text="Mode: Automatic")
            self.mqtt_handler.client.publish("iot/device/mode", "auto")
        else:
            self.device.set_manual_mode()
            self.status_label.config(text="Mode: Manual")
            self.mqtt_handler.client.publish("iot/device/mode", "manual")

    def update_data(self):
        self.device.update_moisture()
        self.device.auto_check()
        self.moisture_value.config(text=f"{self.device.moisture_level}%")

        self.mqtt_handler.publish_data()

        if self.device.pump_on:
            self.pump_button.config(bg="green", text="Pump ON")
        else:
            self.pump_button.config(bg="red", text="Pump OFF")

        self.root.after(10000, self.update_data)

root = tk.Tk()
device = IoTDevice()
mqtt_handler = MQTTHandler(device)
app = IoTApp(root, device, mqtt_handler)
root.mainloop()