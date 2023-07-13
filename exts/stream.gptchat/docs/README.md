# Stream-GPT

Stream-GPT is an Omniverse Extension that uses OpenAI's GPT-3 model to create a virtual assistant. It allows users to interact with the assistant through both text and voice, and the assistant responds in kind. The extension uses OpenAI's Whisper ASR system to transcribe audio input and Eleven Labs' API to convert the assistant's text responses into audio.

## Getting Started

### Prerequisites

- OpenAI API key
- Eleven Labs API key

### SET UP

1. Set your OpenAI and Eleven Labs API keys, as well as the voice_id, model_id, and the Audio2Face's audioplayer's prim path (instance_name)  in the extension's settings:

- Open the extension and click on the "Settings" button.
- Enter your OpenAI API key, Eleven Labs API key, voice_id, model_id and instance name in the corresponding fields. (A text file in the repository lists the available voice ids.)


## Usage

Once the application is running, you can interact with the virtual assistant through the UI. You can type your prompts into the text field and click on the "Send" button or use the "Record Audio" button to speak your prompts. The assistant will respond in the chat log and through your speakers.

You can also add a system to the GPT virtual assistant by typing it in the "System" field in the UI.

All interactions made with the extension are saved in a folder named "chat_logs" for future reference.


