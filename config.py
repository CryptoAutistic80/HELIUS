import os

# Retrieve Discord bot token from environment variables
TOKEN = os.environ['DISCORD_TOKEN']

# Retrieve OpenAI API key from environment variables
OPENAI_KEY = os.environ['KEY_OPENAI']

# Set the maximum number of retries for failed OpenAI API requests
MAX_RETRIES = 10

# Set the number of chat messages in the chat history
CHAT_HISTORY = 24

# Set the maximum word limit for user messages
MESSAGE_WORD_LIMIT = 80

