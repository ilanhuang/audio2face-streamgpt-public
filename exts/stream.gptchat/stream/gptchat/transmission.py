#Stream-GPT
#GNU - GLP Licence
#Copyright (C) <year>  <Huang I Lan & Erks - Virtual Studio>
#This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#You should have received a copy of the GNU General Public License along with this program.  If not, see <https://www.gnu.org/licenses/>.

import grpc
import os
import soundfile
import numpy as np
import audio2face_pb2
import audio2face_pb2_grpc
import sounddevice as sd
import time
from typing import Iterator
import requests
import queue
import threading
import carb

def generate_stream(text: str, voice_id: str, model_id: str, api_key: str, stream_chunk_size: int = 2048) -> Iterator[bytes]:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    data = dict(text=text, model_id=model_id, voice_settings=None)
    headers = {"xi-api-key": api_key}
    response = requests.post(url, json=data, headers=headers, stream=True)
    for chunk in response.iter_content(chunk_size=stream_chunk_size):
        if chunk:
            yield chunk

def read_api_key_from_file(file_path: str) -> str:
    with open(file_path, 'r') as f:
        return f.read().strip()

def text_to_audio_stream(text, instance_name, api_key):
    print("text_to_audio_stream: start")

    settings = carb.settings.get_settings()
    voice_id = settings.get_as_string("/persistent/exts/omni.example.streamgpt/VOICE_ID")
    model_id = settings.get_as_string("/persistent/exts/omni.example.streamgpt/MODEL_ID")

    audio_stream = generate_stream(text, voice_id, model_id, api_key)

    current_dir = os.path.dirname(os.path.realpath(__file__))
    audio_filename = os.path.join(current_dir, "temp_audio_response.mp3")
    with open(audio_filename, 'wb') as f:
        for chunk in audio_stream:
            f.write(chunk)

    audio_data, samplerate = soundfile.read(audio_filename, dtype="float32")

    if len(audio_data.shape) > 1:
        audio_data = np.average(audio_data, axis=1)

    url = "localhost:50051"

    audio_queue = queue.Queue()
    audio_queue.put(audio_data)

    def audio_streamer():
        while not audio_queue.empty():
            audio_chunk = audio_queue.get()
            push_audio_track_stream(url, audio_chunk, samplerate, instance_name)

    audio_thread = threading.Thread(target=audio_streamer)
    audio_thread.start()

    os.remove(audio_filename)

    print("text_to_audio_stream: end")

def push_audio_track_stream(url, audio_data, samplerate, instance_name):
    print("push_audio_track_stream: start")

    chunk_size = samplerate // 10
    sleep_between_chunks = 0.04

    with grpc.insecure_channel(url) as channel:
        print("Channel created")
        stub = audio2face_pb2_grpc.Audio2FaceStub(channel)

        def make_generator():
            start_marker = audio2face_pb2.PushAudioRequestStart(
                samplerate=samplerate,
                instance_name=instance_name,
                block_until_playback_is_finished=False,
            )
            yield audio2face_pb2.PushAudioStreamRequest(start_marker=start_marker)
            for i in range(len(audio_data) // chunk_size + 1):
                try:
                    time.sleep(sleep_between_chunks)
                    chunk = audio_data[i * chunk_size : i * chunk_size + chunk_size]
                    yield audio2face_pb2.PushAudioStreamRequest(audio_data=chunk.astype(np.float32).tobytes())
                except Exception as e:
                    print(f"Error in generator function: {e}")
                    break

        request_generator = make_generator()
        print("Sending audio data...")
        response = stub.PushAudioStream(request_generator)
        if response.success:
            print("SUCCESS")
        else:
            print(f"ERROR: {response.message}")
    print("Channel closed")