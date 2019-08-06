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


mqtt_client = mqtt.Client()

if __name__ == "__main__":
         mqtt_client.on_connect = on_connect
         mqtt_client.message_callback_add("hermes/intent/test12345:play/#", play)
         mqtt_client.connect("localhost", 1883)
         mqtt_client.loop_forever()

