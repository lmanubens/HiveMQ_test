import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import json, time, random
from collections import deque

BROKER = "broker.hivemq.com"
FOUND_TOPICS = set()
MAX_POINTS = 300
data = deque(maxlen=MAX_POINTS)

#####################################
# discover 'vibration' topics
#####################################
def discover_vibration_topics(duration=5):
    def on_message(client, userdata, msg):
        #print(msg.topic.lower())
        if "adxl362/" in msg.topic.lower():
            FOUND_TOPICS.add(msg.topic)

    client = mqtt.Client()
    client.on_message = on_message
    client.connect(BROKER, 1883, 60)
    client.subscribe("sensor/#")
    client.loop_start()

    print(f"Scanning for vibration topics ({duration}s)...")
    time.sleep(duration)

    client.loop_stop()
    client.disconnect()

    return list(FOUND_TOPICS)

topics = discover_vibration_topics()

if not topics:
    print("\nNo vibration topics found. Try again or increase duration.")
    exit()

selected_topic = random.choice(topics)
print("\nRandomly selected vibration topic:", selected_topic)

#####################################
# real-time plotting
#####################################
def on_connect(client, userdata, flags, rc):
    client.subscribe(selected_topic)
    print("Subscribed to:", selected_topic)

def on_message_plot(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        print(payload)
        # Try JSON first
        try:
            value = json.loads(payload)
            # handle various formats
            if isinstance(value, dict):
                value = list(value.values())[0]
            value = float(value)
        except:
            # Raw numeric string
            value = float(payload)
        #print(value)
        data.append(value)
    except:
        pass

# MQTT client for real-time plotting
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message_plot
client.connect(BROKER, 1883, 60)
client.loop_start()

# Matplotlib setup
fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)
#ax.set_ylim(-10, 10)  # adjustable range
ax.set_xlim(0, MAX_POINTS)
ax.set_title(f"Real-time MQTT vibration data\n{selected_topic}")

def update(frame):
    if data:
        ymin = min(data)
        ymax = max(data)
        padding = (ymax - ymin) * 0.5
        ax.set_ylim(ymin - padding, ymax + padding)
        line.set_data(range(len(data)), list(data))
    return line

ani = FuncAnimation(fig, update, interval=100)
plt.tight_layout()
plt.show()

client.loop_stop()
client.disconnect()
