import tkinter as tk
import paho.mqtt.client as mqtt

class IoTDevice:
    def __init__(self):
        self.moisture_level = 100
        self.manual_mode = True
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
        self.pump_on = False

    def set_auto_mode(self):
        self.manual_mode = False
        self.pump_on = False

    def auto_check(self):
        if not self.manual_mode:
            if self.moisture_level < 30:
                self.pump_on = True
            elif self.moisture_level > 70:
                self.pump_on = False

class MQTTHandler:
    def __init__(self, device):
        self.device = device
        self.client = mqtt.Client(protocol=mqtt.MQTTv5)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect("test.mosquitto.org", 1883, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc, properties=None):
        print("Connected to MQTT server with result code " + str(rc))
        self.client.subscribe("iot/device/control")
        self.client.subscribe("iot/device/mode")

    def on_message(self, client, userdata, msg):
        print(f"Received message '{msg.payload.decode()}' on topic '{msg.topic}'")
        if msg.topic == "iot/device/control":
            if msg.payload.decode() == "toggle_pump" and self.device.manual_mode:
                self.device.toggle_pump()
        elif msg.topic == "iot/device/mode":
            if msg.payload.decode() == "manual":
                self.device.set_manual_mode()
                print("Switched to manual mode.")
            elif msg.payload.decode() == "auto":
                self.device.set_auto_mode()
                print("Switched to automatic mode.")

    def publish_data(self):
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

        self.status_label = tk.Label(root, text="Mode: Manual")
        self.status_label.pack()

        self.update_data()

    def update_data(self):
        self.device.update_moisture()
        self.device.auto_check()
        self.moisture_value.config(text=f"{self.device.moisture_level}%")

        self.mqtt_handler.publish_data()

        if self.device.manual_mode:
            self.status_label.config(text="Mode: Manual")
        else:
            self.status_label.config(text="Mode: Automatic")

        # Отображение состояния помпы
        if self.device.pump_on:
            self.moisture_value.config(bg="lightblue")
        else:
            self.moisture_value.config(bg="white")

        self.root.after(10000, self.update_data)

root = tk.Tk()
device = IoTDevice()
mqtt_handler = MQTTHandler(device)
app = IoTApp(root, device, mqtt_handler)
root.mainloop()
