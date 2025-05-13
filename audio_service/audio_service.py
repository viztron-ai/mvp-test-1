import random, json, os, pyaudio, wave, time, paho.mqtt.client as mq
from whisper import load_model
BROKER=os.getenv("MQTT_HOST","mosquitto")
whisper=load_model("tiny-int8")
p=pyaudio.PyAudio()
def play(f):
  w=wave.open(f,'rb'); s=p.open(format=p.get_format_from_width(w.getsampwidth()),
  channels=w.getnchannels(),rate=w.getframerate(),output=True)
  d=w.readframes(4096); 
  while d: s.write(d); d=w.readframes(4096); s.close()
def rec(out="/tmp/r.wav"):
  s=p.open(format=pyaudio.paInt16,channels=1,rate=16000,input=True,frames_per_buffer=2048)
  frames=[s.read(2048) for _ in range(16000//2048*3)]; s.stop_stream(); s.close()
  w=wave.open(out,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
  w.writeframes(b''.join(frames)); w.close()
def on_m(c,u,m):
  id=m.topic.split("/")[-1]
  play(f"/srv/prompts/{random.choice(os.listdir('/srv/prompts'))}")
  rec(); txt=whisper.transcribe("/tmp/r.wav")["text"].lower()
  tone="negative" if any(k in txt for k in["angry","attack","get back"]) else "neutral"
  c.publish(f"vz/audio/{id}",json.dumps({"id":id,"transcript":txt,"tone":tone}))
cli=mq.Client(); cli.on_message=on_m; cli.connect(BROKER,1883)
cli.subscribe("vz/inquiry/#"); cli.loop_forever()
