#import ctypes.util
#orig_ctypes_util_find_library = ctypes.util.find_library
#def proxy_find_library(lib):
#    if lib == 'fluidsynth':
#        return 'libfluidsynth.so.1'
#    else:
#        return orig_ctypes_util_find_library(lib)
#ctypes.util.find_library = proxy_find_library

import magenta
import note_seq
import tensorflow
from note_seq.protobuf import music_pb2

from flask import Flask
from flask import request
from flask import json

import boto3
import requests

from midi2audio import FluidSynth

app = Flask(__name__)

import setup
import os


session = boto3.Session(
	aws_access_key_id=setup.ACCESS_KEY,
	aws_secret_access_key=setup.SECRET_ACCESS_KEY
)
# client = session.client('s3')
s3 = session.resource('s3')

@app.route('/', methods=['GET'])
def home():
	dt = {
		"message": "Checking response"
	}
	return json.dumps(dt)

@app.route('/notes/new/', methods=['POST'])
def fn():
	payload = json.loads(request.get_data().decode('utf-8'))
	notes_sequence = music_pb2.NoteSequence()

	uuid = payload["uuid"]

	text = payload["details"]
	divider = -1
#	print(payload)
	if payload["tone"] == "Happy" or payload["tone"] == "Surprise":
		divider = 2
	if payload["tone"] == "Angry":
		divider = 3
	if payload["tone"] == "Fear" or payload["tone"] == "Sad":
		divider = 4

	newText = ''
	for i in text:
		if i.isalnum() or i == ' ':
			newText += i
	txtLs = newText.split(" ")
	noteSeqLen = []

	for i in txtLs:
		res = 0
		for j in i:
			res += int(ord(j))
		noteSeqLen.append(round(res / len(i)) - 40)

	for i in range(len(noteSeqLen)):
		notes_sequence.notes.add(pitch=noteSeqLen[i], start_time=round((i / divider), 2), end_time=(round((i / divider), 2) + (1 / divider)), velocity=80)

	notes_sequence.total_time = round(len(noteSeqLen) // divider) + 1
	notes_sequence.tempos.add(qpm=60)

	note_seq.sequence_proto_to_midi_file(notes_sequence, uuid + '.mid')
	fs = FluidSynth()
	fs.midi_to_audio(uuid +'.mid', uuid + '.wav')

#	content_type = request.mimetype

#	client.put_object(
#		Body = open(uuid + '.wav').read(),
#		Bucket = 'kalpanageneratedaudios',
#		Key = uuid + '.wav'
#	)
	s3.Bucket('kalpanageneratedaudios').upload_file(uuid + '.wav', uuid + '.wav')
#	s3.Bucket('kalpanageneratedaudios').upload_file(uuid + '.mid', uuid + '.mid')
	os.remove(uuid + '.mid')
	os.remove(uuid + '.wav')

	djangoServerURL = 'http://localhost:8000/note/update/'

	resultObj = {
		"uuid": uuid,
		"message": "Successful"
	}
	requests.post(djangoServerURL, data = json.dumps(resultObj))

	return json.dumps({
		"message": "Processed"
	})

app.run(host='0.0.0.0', port='3000')
