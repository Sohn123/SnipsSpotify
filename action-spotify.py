#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
from hermes_python.hermes import Hermes
from hermes_python.ffi.utils import MqttOptions
from hermes_python.ontology import *
import paho.mqtt.client as mqtt
import json
import io

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

class SnipsConfigParser(configparser.SafeConfigParser):
    def to_dict(self):
        return {section : {option_name : option for option_name, option in self.items(section)} for section in self.sections()}


def read_configuration_file(configuration_file):
    try:
        with io.open(configuration_file, encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            conf_parser = SnipsConfigParser()
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, configparser.Error) as e:
        return dict()

def on_connect(client, userdata, flags, rc):
    client.subscribe("hermes/intent/#")
def play(client, userdata, msg):
    data = json.loads(msg.payload.decode("utf-8"))
    session_id = data['sessionId']
    say(session_id, "der Song wird fortgesetzt")
    MM2("SPOTIFY_PLAY", {"uris": ["spotify:track:4iV5W9uYEdYUVa79Axb7Rh", "spotify:track:1301WleyT98MSxVHPZCA6M"]})  
def search(client, userdata, msg):
    data = json.loads(msg.payload.decode("utf-8"))
    session_id = data['sessionId']
    slots = {slot['slotName']: slot['value']['value'] for slot in data['slots']}
    print(slots)
    query = '{"type": "'
    i = 0
    for key in slots:
        i = i + 1
        query = query + key 
        if i < len(slots):
           query = query + ","
    query = query + '", "query":"'
    i = 0
    for key in slots:
       i = i + 1
       query = query + slots[key] 
       if i < len(slots):
           query = query + "+"
    query = query + '", "random": "false"}'
    print(query)
    text = "Mache ich"
    say(session_id, text)
    MM2search("SPOTIFY_SEARCH", query)

def MM2search(intentname, action):
    mqtt_client.publish(("external/MagicMirror2/Spotify/" + intentname),
                        action)
    print(json.dumps(action))
def MM2(intentname, action):
    mqtt_client.publish(("external/MagicMirror2/Spotify/" + intentname),
                        json.dumps(action))
    print(json.dumps(action))

def say(session_id, text):
    mqtt_client.publish('hermes/dialogueManager/endSession',
                        json.dumps({'text': text, "sessionId": session_id}))


mqtt_client = mqtt.Client()

if __name__ == "__main__":
         mqtt_client.on_connect = on_connect
         mqtt_client.message_callback_add("hermes/intent/sohn:play/#", play)
         mqtt_client.message_callback_add("hermes/intent/sohn:playResource/#", search)
         mqtt_client.connect("localhost", 1883)
         mqtt_client.loop_forever()
