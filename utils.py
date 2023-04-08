import json
import asyncio
from discord.errors import NotFound
from config import CHAT_HISTORY

# Load prompt parameters from a JSON file
def load_prompt_parameters(filename):
    with open(filename, 'r') as file:
        return json.load(file)

# Add a chat message to the user's chat history
def add_chat_history(user_id, author, content, user_chat_histories):
    # Initialize the user's chat history if it doesn't exist
    if user_id not in user_chat_histories:
        user_chat_histories[user_id] = []

    # Add the chat message to the history
    user_chat_histories[user_id].append({"role": "user", "content": content})

    # Keep only the last CHAT_HISTORY messages
    user_chat_histories[user_id] = user_chat_histories[user_id][-CHAT_HISTORY:]

# End a chat after a specified timeout due to inactivity
async def end_inactive_chat(user_id, channel, active_threads, timeout=60):
    # Wait for the specified timeout
    await asyncio.sleep(timeout)

    # If the user is not in active_threads, do nothing
    if user_id not in active_threads:
        return

    try:
        # Delete the chat channel
        await channel.delete()
    except NotFound:
        print(f"Channel not found for user {user_id}. It may have been deleted by another process.")
    except Exception as e:
        print(f"Error occurred while deleting the channel for user {user_id}: {e}")

    # Remove the user from the active_threads set
    active_threads.discard(user_id)


