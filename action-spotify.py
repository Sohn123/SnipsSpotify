#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import configparser
from hermes_python.ontology import *
import paho.mqtt.client as mqtt
import json
import io
import sys
import spotipy
import spotipy.oauth2 as oauth2
import spotipy.util as util
import spotipy.client as client
scope = 'user-library-read user-top-read user-read-recently-played streaming app-remote-control user-follow-read user-follow-modify user-read-playback-state user-read-currently-playing user-modify-playback-state'

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

mqtt_client = mqtt.Client()
was_paused = False
vorlage = {'operations': [['add', {'snips/default--track': []}], ['add', {'snips/default--album': []}], ['add', {'snips/default--artist': []}]]}

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
    client.subscribe("hermes/hotword/default/#")
    client.subscribe("hermes/dialogueManager/#")


if len(sys.argv) > 1:
    username = sys.argv[1]
else:
    print("Usage: %s username") 
    
    sys.exit()

token = util.prompt_for_user_token(username, scope)

def play(client,userdata,msg):
    data = json.loads(msg.payload.decode("utf-8"))
    session_id = data['sessionId']

    if token:
        sp = spotipy.Spotify(auth=token)
        if is_active(sp, session_id) == 0:
            return
        say(session_id, "Die Wiedergabe wird fortgesetzt")
        sp.start_playback()


def search(client, userdata, msg):
   if token:
       data = json.loads(msg.payload.decode("utf-8"))
       session_id = data['sessionId']
       print(data['slots'])
       slots = {slot['slotName']: slot['value']['value'] for slot in data['slots']}
       if len(slots) == 0:
           say(session_id, "ich habe dich nicht verstanden")
           time.sleep(3)
           return
       print(slots)
       art = ""
       query = ""
       i = 0
       for key in slots:
           i = i +1
           query = query + slots[key]
           art = art + key
           if i < len(slots):
              query = query + " "
              art = art + ","
       sp = spotipy.Spotify(auth=token)
       if is_active(sp, session_id) == 0:
            return
       result = sp.search(q=query,limit=1, type=art)
       if 'tracks' in result:
          uri = result['tracks']['items'][0]['uri']
          print(uri)
          tracks = [uri]
          print(tracks)
          sp.start_playback(uris=tracks)
          say(session_id, "wird erledigt")
       elif 'albums' in result:
           uri = result['albums']['items'][0]['uri']
           sp.start_playback(context_uri=uri)
           say(session_id, "wird erledigt")
       elif 'artists' in result:
           uri = result['artists']['items'][0]['uri']
           sp.start_playback(context_uri=uri)
           say(session_id, "wird erledigt")
       elif 'playlists' in result:
           uri = result['playlists']['items'][0]['uri']
           sp.start_playback(context_uri=uri)
           say(session_id, "wird erledigt")
   else:
       print("Can't get token for " + username)


def name_hinzufuegen(result):
    for i in result['items']:
        vorlage['operations'][0][1]['snips/default--track'].append(i['track']['name'])

def say(session_id, text):
    mqtt_client.publish('hermes/dialogueManager/endSession',
                        json.dumps({'text': text, "sessionId": session_id}))
def aktualisierung(client, userdata, msg):
    data = json.loads(msg.payload.decode("utf-8"))
    session_id = data['sessionId']
    slots = {slot['slotName']: slot['value']['value'] for slot in data['slots']}
    if token:
        sp = spotipy.Spotify(auth=token)
        if is_active(sp, session_id) == 0:
            return
        result = sp.current_user_saved_tracks()
        name_hinzufuegen(result)
        result2 = sp.current_user_top_tracks(limit=50, time_range='medium_term')
        for z in result2['items']:
            vorlage['operations'][0][1]['snips/default--track'].append(z['name'])
        result3 = sp.current_user_recently_played(limit=50)
        name_hinzufuegen(result3)
        result4 = sp.current_user_saved_albums(limit=20, offset=0)
        for z in result4['items']:
            vorlage['operations'][1][1]['snips/default--album'].append(z['album']['name'])
        result5 = sp.current_user_top_artists(limit=50,)
        for k in result5['items']:
            vorlage['operations'][2][1]['snips/default--artist'].append(k['name'])
        result6 = sp.current_user_followed_artists(limit=50)
        print(result6['artists']['items'][0]['name'])
        for u in result6['artists']['items']:
            vorlage['operations'][2][1]['snips/default--artist'].append(u['name'])

        mqtt_client.publish('hermes/injection/perform', json.dumps(vorlage))
        say(session_id, "Mein Wortschatz wurde aktualisiert", )
    else:
        print("Can't get token for " + username)

def volume_down(client, userdata, msg):
    data = json.loads(msg.payload.decode("utf-8"))
    session_id = data['sessionId']
    slots = {slot['slotName']: slot['value']['value'] for slot in data['slots']}
    if token:
        sp = spotipy.Spotify(auth=token)
        if is_active(sp, session_id) == 0:
            return
        result = sp.current_playback()
        actual_volume = result['device']['volume_percent']
        new_volume= actual_volume - 10
    try:
        sp.volume(new_volume)
        print("die Lautstärke wurde auf "+ str(new_volume))
        say(session_id, "die Lautstärke wurde auf "+ str(new_volume) + " gesetzt")
    except:
        print("Eine Lautstärkeanpassung ist für dieses Gerät nicht möglich")
        say(session_id, "Eine Lautstärkeanpassung ist für dieses Gerät nicht möglich")
    else:
        print('Es ist kein valider Token da')

def volume_up(client, userdata, msg):
    data = json.loads(msg.payload.decode("utf-8"))
    session_id = data['sessionId']
    slots = {slot['slotName']: slot['value']['value'] for slot in data['slots']}
    if token:
        sp = spotipy.Spotify(auth=token)
        if is_active(sp, session_id) == 0:
            return
        result = sp.current_playback()
        actual_volume = result['device']['volume_percent']
        new_volume= actual_volume + 10
    try:
        sp.volume(new_volume)
        print("die Lautstärke wurde auf "+ str(new_volume))
        say(session_id, "die Lautstärke wurde auf "+ str(new_volume) + " gesetzt")
    except:
        print("Eine Lautstärkeanpassung ist für dieses Gerät nicht möglich")
        say(session_id, "Eine Lautstärkeanpassung ist für dieses Gerät nicht möglich")
    else:
        print('Es ist kein valider Token da')

def deactivate_spotify(client, userdata, msg):
    print("toll")
    if token:
        sp =spotipy.Spotify(auth=token)
        if is_active(sp, 'lol') == 0:
            return
        result= sp.current_playback()
        is_playing = result['is_playing']
        device_id = result['device']['id']
        if is_playing == True and device_id == "98bb0735e28656bac098d927d410c3138a4b5bca":
            sp.pause_playback(device_id="98bb0735e28656bac098d927d410c3138a4b5bca")

            global was_paused
            was_paused = True

def activate_spotify(client, userdata, msg):
    if token:
        global was_paused
        if was_paused == True:
            sp = spotipy.Spotify(auth=token)
            if is_active(sp, 'lol') == 0:
                return
            sp.start_playback(device_id="98bb0735e28656bac098d927d410c3138a4b5bca")
            was_paused = False


def previous_song(client, userdata, msg):
    data = json.loads(msg.payload.decode("utf-8"))
    session_id = data['sessionId']
    if token:
        sp = spotipy.Spotify(auth=token)
        if is_active(sp, session_id) == 0:
            return
        say(session_id, "Es wurde ein Song zurückgespult")
        sp.previous_track()

def next_song(client, userdata, msg):
    data = json.loads(msg.payload.decode("utf-8"))
    session_id = data['sessionId']
    if token:
        sp = spotipy.Spotify(auth=token)
        if is_active(sp, session_id) == 0:
            return
        say(session_id, "Es wurde ein Song vorgespult")
        sp.next_track()
def shuffle(client, userdata, msg):
    if token:
        data = json.loads(msg.payload.decode("utf-8"))
        session_id = data['sessionId']
        slots = {slot['slotName']: slot['value']['value'] for slot in data['slots']}
        print(slots)
        sp = spotipy.Spotify(auth= token)
        if is_active(sp, session_id) == 0:
            return
        if slots['mode'] == "true":
            sp.shuffle(True)
        else:
            sp.shuffle(False)
def repeat(client, userdata, msg):
    if token:
        data = json.loads(msg.payload.decode("utf-8"))
        session_id = data['sessionId']
        slots = {slot['slotName']: slot['value']['value'] for slot in data['slots']}
        sp = spotipy.Spotify(auth=token)
        if is_active(sp, session_id) == 0:
            return
        print(slots['repeat_mode'])
        sp.repeat(slots['repeat_mode'])

def pause(client, userdata, msg):
    data = json.loads(msg.payload.decode("utf-8"))
    session_id = data['sessionId']
    if token:
        sp = spotipy.Spotify(auth=token)
        if is_active(sp, session_id) == 0:
            return
        sp.pause_playback()
        global was_paused
        was_paused = False
        say(session_id, "Der song wurde pausiert")

def is_active(sp, session_id):
    result = sp.devices()
    print(result)
    id = os.getenv('SPOTIPY_CLIENT_ID')
    secret= os.getenv('SPOTIPY_CLIENT_SECRET')
    url = os.getenv('SPOTIPY_REDIRECT_URI')
    spo = oauth2.SpotifyOAuth(id, secret, url, scope=scope)
    with open('.cache-alexander.sohn642@gmail.com') as json_file:
        data = json.load(json_file)
        refresh = data['refresh_token']
        if spo.is_token_expired(data) == True:
            spo.refresh_access_token(refresh)
    for i in result['devices']:
        if i['is_active'] == True:
                return 1
    if session_id != 'lol':
        say(session_id, "Momentan steht leider kein Spotify Player zur Verfügung")
    return 0

#spo = oauth2.SpotifyOAuth(scope=scope, cache_path= './')
id = os.getenv('SPOTIPY_CLIENT_ID')
secret= os.getenv('SPOTIPY_CLIENT_SECRET')
url = os.getenv('SPOTIPY_REDIRECT_URI')
spo = oauth2.SpotifyOAuth(id, secret, url, scope=scope)
with open('.cache-alexander.sohn642@gmail.com') as json_file:
    data = json.load(json_file)
    refresh = data['refresh_token']
spo.refresh_access_token(refresh)

if __name__ == "__main__":
         mqtt_client.on_connect = on_connect
         mqtt_client.message_callback_add("hermes/intent/sohn:play/#", play)
         mqtt_client.message_callback_add("hermes/intent/sohn:playResource/#", search)
         mqtt_client.message_callback_add("hermes/intent/sohn:aktualisierung", aktualisierung)
         mqtt_client.message_callback_add("hermes/intent/sohn:volume_down", volume_down)
         mqtt_client.message_callback_add("hermes/intent/sohn:volume_up", volume_up)
         mqtt_client.message_callback_add("hermes/hotword/default/detected", deactivate_spotify)
         mqtt_client.message_callback_add("hermes/dialogueManager/endSession", activate_spotify)
         mqtt_client.message_callback_add("hermes/intent/sohn:previous", previous_song)
         mqtt_client.message_callback_add("hermes/intent/sohn:next", next_song)
         mqtt_client.message_callback_add("hermes/intent/sohn:shuffleMode", shuffle)
         mqtt_client.message_callback_add("hermes/intent/sohn:repeatMode", repeat)
         mqtt_client.message_callback_add("hermes/intent/sohn:pause", pause)
         mqtt_client.connect("192.168.178.52", 1883)
         mqtt_client.loop_forever()

