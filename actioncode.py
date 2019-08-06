import paho.mqtt.client as mqtt
import json


def on_connect(client, userdata, flags, rc):
    client.subscribe("hermes/intent/#")
def play(client, userdata, msg):
    data = json.loads(msg.payload.decode("utf-8"))
    session_id = data['sessionId']
    MM2('play', {})
    say(session_id, "der Song wird fortgesetzt")

def MM2(intentname, action):
    mqtt_client.publish(('external/MagicMirror2/HideShowMove/' + intentname),
                        json.dumps(action))
def say(session_id, text):
    mqtt_client.publish('hermes/dialogueManager/endSession',
                        json.dumps({'text': text, "sessionId": session_id}))


client = mqtt.Client()

if __name__ == "__main__":
         client.on_connect = on_connect
         client.message_callback_add("hermes/intent/sohn:play/#", play)

