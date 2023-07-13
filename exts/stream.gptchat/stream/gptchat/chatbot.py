#Stream-GPT
#GNU - GLP Licence
#Copyright (C) <year>  <Huang I Lan & Erks - Virtual Studio>
#This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#You should have received a copy of the GNU General Public License along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import openai
import json
import numpy as np
from numpy.linalg import norm
import re
from time import time,sleep
from uuid import uuid4
import datetime


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)


def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return json.load(infile)


def save_json(filepath, payload):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        json.dump(payload, outfile, ensure_ascii=False, sort_keys=True, indent=2)


def timestamp_to_datetime(unix_time):
    return datetime.datetime.fromtimestamp(unix_time).strftime("%A, %B %d, %Y at %I:%M%p %Z")


def gpt3_embedding(content, engine='text-embedding-ada-002'):
    content = content.encode(encoding='ASCII',errors='ignore').decode()  # fix any UNICODE errors
    response = openai.Embedding.create(input=content,engine=engine)
    vector = response['data'][0]['embedding']  # this is a normal list
    return vector

def chatgpt_completion(messages, model="gpt-4", temp=0.0, top_p=1.0, tokens=400, freq_pen=0.0, pres_pen=0.0):
    response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
                top_p=top_p,
                frequency_penalty=freq_pen,
                presence_penalty=pres_pen,)
        
    text = response['choices'][0]['message']['content']
    
    tokens_used = response['usage']['total_tokens']

    filename = 'chat_%s_aibot.json' % time()
    script_dir = os.path.dirname(os.path.realpath(__file__))
    chat_logs_path = os.path.join(script_dir, 'chat_logs')
    if not os.path.exists(chat_logs_path):
        os.makedirs(chat_logs_path)

    input_message = messages[-1]['content']
    log_content = f"User:\n{input_message}\n\nAi_Bot:\n{text}\n\nTokens used: {tokens_used}"
    save_file(os.path.join(chat_logs_path, filename), log_content)

    return text
    

def flatten_convo(conversation):
    convo = ''
    for i in conversation:
        convo += '%s: %s\n' % (i['role'].upper(), i['content'])
    return convo.strip()

def set_openai_api_key(api_key):
    openai.api_key = api_key

def set_system_content(content):
    global system_content
    system_content = content
    
if __name__ == '__main__':
    convo_length = 30
    set_openai_api_key(api_key)
    conversation = list()
    conversation.append({'role': 'system', 'content': system_content})
    counter = 0
    
    while True:
        # get user input, save to file
        a = input('\n\nCLIENT: ')
        conversation.append({'role': 'user', 'content': a})
        filename = 'chat_%s_client.txt' % time()
        if not os.path.exists('chat_logs'):
            os.makedirs('chat_logs')
        save_file('chat_logs/%s' % filename, a)
        flat = flatten_convo(conversation)
        # generate a response
        response = chatgpt_completion(conversation)
        conversation.append({'role': 'assistant', 'content': response})
        print('\n\nAI_Bot: %s' % response)
        # increment counter and consolidate memories
        counter += 2
        if counter >= 10:
            # reset conversation
            conversation = list()
            conversation.append({'role': 'system', 'content': system_content})
            
            
         