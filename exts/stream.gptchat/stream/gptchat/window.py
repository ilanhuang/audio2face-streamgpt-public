#Stream-GPT
#GNU - GLP Licence
#Copyright (C) <year>  <Huang I Lan & Erks - Virtual Studio>
#This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#You should have received a copy of the GNU General Public License along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import omni.ui as ui
import omni.kit.commands
from omni.kit.window.popup_dialog.form_dialog import FormDialog
from time import time
from .recording_transcription import record_client_voice, transcribe_audio_to_text
from .chatbot import chatgpt_completion, set_system_content
from .transmission import text_to_audio_stream
import threading
import time
import tempfile
import datetime
import carb
                    
def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

def timestamp_to_datetime(unix_time):
    return datetime.datetime.fromtimestamp(unix_time).strftime("%A, %B %d, %Y at %I:%M%p %Z")

class AudioChatWindow(ui.Window):

    def _build_fn(self):
        with self.frame:
            with ui.VStack():
                with ui.ScrollingFrame(height=ui.Percent(75)):
                    self.chat_log = ui.Label("", word_wrap=True)
                with ui.HStack(height=ui.Percent(10)):
                    ui.StringField(model=self._prompt_model, multiline=True)
                with ui.HStack(height=ui.Percent(10)):
                    self.record_audio_button = ui.Button("Record Audio", height=40, clicked_fn=lambda *_args, **_kwargs: self._toggle_record_audio())
                    ui.Button("Send", height=40, clicked_fn=lambda: self._send_text_prompt())
                with ui.HStack():
                    ui.Button("Settings", tooltip="Configure API Key, Instance name and Default System", width=0, height=0, clicked_fn=lambda: self._open_settings())
                    system_settings_button = ui.Button("System", height=0, width=0)
                    system_settings_button.set_clicked_fn(lambda: self.show_system_settings_menu())
                    
    def __init__(self, title: str, **kwargs) -> None:
        self.conversation = [{"role": "system", "content": ""}]
        self.system_content_model = ui.SimpleStringModel()
        self.lock = threading.Lock()
        super().__init__(title, **kwargs)
        self._prompt_model = ui.SimpleStringModel()
        self.frame.set_build_fn(self._build_fn)
    
    def show_system_settings_menu(self):
        self.system_settings_menu = ui.Menu("")
        with self.system_settings_menu:
            ui.StringField(model=self.system_content_model, multiline=True)
        self.system_settings_menu.show()                    
    
    def _toggle_record_audio(self):
        if not hasattr(self, "recording"):
            self.recording = False

        if not self.recording:
            self.recording = True
            threading.Thread(target=self._record_and_transcribe_audio).start()
        else:
            self.recording = False
    
    def _process_conversation(self, user_content):
        current_system_content = self.system_content_model.get_value_as_string().strip()
        if current_system_content != self.conversation[0]['content']:
            self.reset_chat()

        set_system_content(current_system_content)
        self.conversation.append({"role": "user", "content": user_content})
        
        response = chatgpt_completion(self.conversation)
        self.chat_log.text += f"\nUser: {user_content}\nAssistant: {response}"

        settings = carb.settings.get_settings()
        instance_name = settings.get_as_string("/persistent/exts/omni.example.streamgpt/INSTANCE_NAME")
        threading.Thread(target=text_to_audio_stream, args=(response, instance_name, self.get_elevenlabs_api_key())).start()
        
    def _record_and_transcribe_audio(self):
        output_filename = "recorded_audio.wav"
        record_client_voice(output_filename)
        transcript = transcribe_audio_to_text(output_filename)       
        self._send_audio_transcript(transcript)
        
    def _send_audio_transcript(self, transcript):
        self.chat_log.text += "\nThinking..."
        threading.Thread(target=self._process_conversation, args=(transcript,)).start()
    
    def reset_chat(self):
        self.chat_log.text = ""
        self.conversation = [{"role": "system", "content": self.system_content_model.get_value_as_string().strip()}]
    
    def _save_settings(self, dialog):
        values = dialog.get_values()

        settings = carb.settings.get_settings()
        settings.set_string("/persistent/exts/omni.example.streamgpt/APIKey_OPEN_AI", values["APIKey_OPEN_AI"])
        settings.set_string("/persistent/exts/omni.example.streamgpt/APIKey_ELEVEN_LABS", values["APIKey_ELEVEN_LABS"])
        settings.set_string("/persistent/exts/omni.example.streamgpt/VOICE_ID", values["ELEVEN_LABS_VOICE_ID"])
        settings.set_string("/persistent/exts/omni.example.streamgpt/MODEL_ID", values["ELEVEN_LABS_MODEL_ID"])
        settings.set_string("/persistent/exts/omni.example.streamgpt/INSTANCE_NAME", values["INSTANCE_NAME"])

        dialog.hide()

    def _open_settings(self):
        settings = carb.settings.get_settings()
        apikey_open_ai = settings.get_as_string("/persistent/exts/omni.example.streamgpt/APIKey_OPEN_AI")
        apikey_eleven_labs = settings.get_as_string("/persistent/exts/omni.example.streamgpt/APIKey_ELEVEN_LABS")
        voice_id = settings.get_as_string("/persistent/exts/omni.example.streamgpt/VOICE_ID")
        model_id = settings.get_as_string("/persistent/exts/omni.example.streamgpt/MODEL_ID")
        instance_name = settings.get_as_string("/persistent/exts/omni.example.streamgpt/INSTANCE_NAME")

        if apikey_open_ai == "":
            apikey_open_ai = "Enter OPEN-AI API Key Here"
        if apikey_eleven_labs == "":
            apikey_eleven_labs = "Enter ELEVEN-LABS API Key Here"
        if instance_name == "":
            instance_name = "Enter Instance Name Here"
        if voice_id == "":
            voice_id = "Enter Eleven Labs Voice ID Here"
        if model_id == "":
            model_id = "Enter Eleven Labs Model ID Here"

        field_defs = [
            FormDialog.FieldDef("APIKey_OPEN_AI", "OPEN-AI API Key: ", ui.StringField, apikey_open_ai),
            FormDialog.FieldDef("APIKey_ELEVEN_LABS", "ELEVEN-LABS API Key: ", ui.StringField, apikey_eleven_labs),
            FormDialog.FieldDef("ELEVEN_LABS_VOICE_ID", "Voice ID: ", ui.StringField, voice_id),
            FormDialog.FieldDef("ELEVEN_LABS_MODEL_ID", "Model ID: ", ui.StringField, model_id),
            FormDialog.FieldDef("INSTANCE_NAME", "Instance Name: ", ui.StringField, instance_name),
        ]

        dialog = FormDialog(
            title="Settings",
            message="Your Settings: ",
            field_defs=field_defs,
            ok_handler=lambda dialog: self._save_settings(dialog))

        dialog.show()
    
    @staticmethod
    def get_openai_api_key():
        settings = carb.settings.get_settings()
        return settings.get_as_string("/persistent/exts/omni.example.streamgpt/APIKey_OPEN_AI")
    
    def get_elevenlabs_api_key(self):
        settings = carb.settings.get_settings()
        return settings.get_as_string("/persistent/exts/omni.example.streamgpt/APIKey_ELEVEN_LABS")       

    def _send_text_prompt(self):
        prompt = self._prompt_model.get_value_as_string()
        self.chat_log.text += "\nThinking..."
        threading.Thread(target=self._process_conversation, args=(prompt,)).start()
        self._prompt_model.set_value("")

    def _toggle_record_audio(self):
        if not hasattr(self, "recording"):
            self.recording = False

        self.recording = not self.recording
        if self.recording:
            self.record_audio_button.text = "Stop Recording"
        else:
            self.record_audio_button.text = "Record Audio"

        threading.Thread(target=self._record_and_transcribe_audio_alternative).start()

    def recording_status(self):
        return self.recording
                
    def _record_and_transcribe_audio_alternative(self):
        with self.lock:
            temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_audio_filename = temp_audio_file.name
            temp_audio_file.close()

            recorded_audio_filename = record_client_voice(temp_audio_filename, self.recording_status)
            transcript = transcribe_audio_to_text(recorded_audio_filename)
            os.remove(temp_audio_filename)

            if transcript.strip():
                self._send_audio_transcript(transcript)

    def destroy(self):
        super().destroy()
        self._prompt_model = None