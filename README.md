# Stream-GPT

Stream-GPT is an Omniverse Extension that uses OpenAI's GPT-3 model to create a virtual assistant. It allows users to interact with the assistant through both text and voice, and the assistant responds in kind. The extension uses OpenAI's Whisper ASR system to transcribe audio input and Eleven Labs' API to convert the assistant's text responses into audio.

## Getting Started

### Prerequisites

- Python 3.6 or higher
- Omniverse Kit
- Omniverse Audio2Face
- OpenAI API key
- Eleven Labs API key

### Installation

1. Clone the repository:

```bash
git clone https://github.com/ilanhuang/audio2face-stream-chatgpt.git
```

2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

3. Update the `sys.path.append` in `extension.py` with the correct path to the `streaming_server` directory in your local clone of the repository.

```python
sys.path.append("C:\\Users\\YourUsername\\path\\to\\stream-gpt\\pkg\\audio2face-2022.2.1\\exts\\omni.audio2face.player\omni\\audio2face\\player\\scripts\\streaming_server")
```

4. Add the custom extension to Omniverse:

- Go to the "Windows" tab on the top of the screen.
- Scroll down to "Extensions".
- Click on the gear icon to open the Extensions settings.
- Click on the "+" button to add a new path to the custom extension.
- A window will pop up when you turn on the extension.

5. Set your OpenAI and Eleven Labs API keys, as well as the voice_id, model_id, and the Audio2Face's audioplayer's prim path (instance_name)  in the extension's settings:

- Open the extension and click on the "Settings" button.
- Enter your OpenAI API key, Eleven Labs API key, voice_id, model_id and instance name in the corresponding fields. (A text file in the repository lists the available voice ids.)


## Usage

Once the application is running, you can interact with the virtual assistant through the UI. You can type your prompts into the text field and click on the "Send" button or use the "Record Audio" button to speak your prompts. The assistant will respond in the chat log and through your speakers.

You can also add a system to the GPT virtual assistant by typing it in the "System" field in the UI.

All interactions made with the extension are saved in a folder named "chat_logs" for future reference.