# **Discord Chatbot with OpenAI GPT**

Welcome to the Discord Chatbot! This chatbot uses OpenAI's GPT-based model to respond to user messages in private threads on Discord. The chatbot is implemented in Python using the **discord.py** library for Discord interactions and the **openai** library for OpenAI API requests.

**Setup**

Before you can run the chatbot, you need to install the required Python packages and set up the necessary environment variables.

**Dependencies**

The chatbot requires the following Python packages:

- **discord.py**
- **openai**

### Environment Variables

You need to set up two environment variables:

- **DISCORD\_TOKEN** : Your Discord bot token
- **KEY\_OPENAI** : Your OpenAI API key

To set these variables, you can either export them in your terminal session or add them to a **.env** file.

### Folder Structure

The chatbot's code is organized into the following files:

- **main.py** : The main script that runs the chatbot
- **config.py** : Contains configuration constants, such as the Discord token and OpenAI API key
- **utils.py** : Contains utility functions for loading prompt parameters and managing chat history
- **ai.py** : Contains the functions for processing API requests and generating responses from the OpenAI API

Ensure that all files are placed in the same directory.

## Running the Chatbot

To run the chatbot, simply execute the **main.py** script

The chatbot should now be running and connected to your Discord server.

## Using the Chatbot

Once the chatbot is up and running, you can use the following commands:

1. !chat
  - Starts a new private thread with the chatbot.
  - Usage: Type "!chat" in any text channel, and the bot will create a private thread for you to chat with it.
2. !end
  - Ends the current private thread with the chatbot and closes it.
  - Usage: Type "!end" within the private thread to close the conversation.

Please note that the chatbot only responds to messages within private threads created using the "!chat" command. If you send messages outside these threads, the chatbot will not respond.

Have a great time chatting with the bot!