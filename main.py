import time
import paho.mqtt.client as mqtt
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, Application
import threading

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC_TELEMETRY = "iot/device/moisture"
MQTT_TOPIC_MODE = "iot/device/mode"
MQTT_TOPIC_CONTROL = "iot/device/control"

TELEGRAM_TOKEN = "7781346961:AAF6-oXHKZmkHVlBGqeNqZ4wSEEsBKe1oyA"

last_moisture = "No data yet"
current_mode = "manual"  # Режим по умолчанию
pump_state = False

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

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code", rc)
    client.subscribe(MQTT_TOPIC_TELEMETRY)
    client.subscribe(MQTT_TOPIC_MODE)

def on_message(client, userdata, msg):
    global last_moisture, current_mode
    print(f"Received message on topic {msg.topic}: {msg.payload.decode()}")
    if msg.topic == MQTT_TOPIC_TELEMETRY:
        last_moisture = msg.payload.decode()
        print(f"Updated moisture level: {last_moisture}")
    elif msg.topic == MQTT_TOPIC_MODE:
        current_mode = msg.payload.decode()
        print(f"Device mode changed to: {current_mode}")

device = IoTDevice()

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

def publish_device_data():
    while True:
        device.update_moisture()
        device.auto_check()

        mqtt_client.publish(MQTT_TOPIC_TELEMETRY, str(device.moisture_level))
        print(f"Published moisture level: {device.moisture_level}")

        time.sleep(5)

def start_mqtt():
    mqtt_client.loop_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Telegram IoT бот. Вот доступные команды:\n"
                                    "/status - Показать текущую влажность\n"
                                    "/set_manual - Установить ручной режим\n"
                                    "/set_auto - Установить автоматический режим\n"
                                    "/toggle_pump - Включить/выключить помпу")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Текущая влажность: {device.moisture_level}%\n"
        f"Режим работы: {'Автоматический' if not device.manual_mode else 'Ручной'}\n"
        f"Помпа: {'Включена' if device.pump_on else 'Выключена'}"
    )


async def set_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    device.set_manual_mode()
    mqtt_client.publish(MQTT_TOPIC_MODE, "manual")
    await update.message.reply_text("Режим работы установлен на: Ручной")

async def set_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    device.set_auto_mode()
    mqtt_client.publish(MQTT_TOPIC_MODE, "auto")
    await update.message.reply_text("Режим работы установлен на: Автоматический")

async def toggle_pump(update: Update, context: ContextTypes.DEFAULT_TYPE):
    device.toggle_pump()
    mqtt_client.publish(MQTT_TOPIC_CONTROL, "toggle_pump")
    state = "ON" if device.pump_on else "OFF"
    await update.message.reply_text(f"Помпа переключена в состояние: {state}")


telemetry_thread = threading.Thread(target=publish_device_data)
telemetry_thread.daemon = True
telemetry_thread.start()

mqtt_thread = threading.Thread(target=start_mqtt)
mqtt_thread.daemon = True
mqtt_thread.start()

application = Application.builder().token(TELEGRAM_TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("status", status))
application.add_handler(CommandHandler("set_manual", set_manual))
application.add_handler(CommandHandler("set_auto", set_auto))
application.add_handler(CommandHandler("toggle_pump", toggle_pump))

print("Бот запущен!")
application.run_polling()
