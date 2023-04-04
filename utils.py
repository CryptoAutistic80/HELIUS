import json

def load_prompt_parameters(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def add_chat_history(user_id, author, content, user_chat_histories):
    if user_id not in user_chat_histories:
        user_chat_histories[user_id] = []
    user_chat_histories[user_id].append({"role": "user", "content": content})
    user_chat_histories[user_id] = user_chat_histories[user_id][-24:]
