import os, json, paho.mqtt.client as mqtt
import RPi.GPIO as GPIO

THR=float(os.getenv("THRESHOLD",0.6)); PIN=int(os.getenv("GPIO_PIN",17))
GPIO.setmode(GPIO.BCM); GPIO.setup(PIN,GPIO.OUT); GPIO.output(PIN,0)
scores={}
def alert(d): print("🔔 ALERT",d); GPIO.output(PIN,1)
def on_vid(cli,ud,msg):
    d=json.loads(msg.payload); id=d["id"]=d.get("id",msg.mid)
    s=d.get("confidence",0)+0.5*(d.get("extras",{}).get("weapon",False))
    scores[id]=s; 
    if 0.3<s<THR: cli.publish(f"vz/inquiry/{id}","")  # trigger voice
    if s>=THR: alert(d)
def on_audio(cli,ud,msg):
    a=json.loads(msg.payload); id=a["id"]; bump=0
    if a["tone"]=="negative": bump+=0.3
    elif "delivery" in a["transcript"]: bump-=0.2
    scores[id]=scores.get(id,0)+bump
    if scores[id]>=THR: alert(a)
cli=mqtt.Client(); cli.connect(os.getenv("MQTT_HOST","mosquitto"),1883)
cli.message_callback_add("vz/audio/#",on_audio)
cli.subscribe(os.getenv("MQTT_TOPIC","frigate/events/#")); cli.on_message=on_vid
cli.loop_forever()
