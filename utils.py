import json
import asyncio
from discord.errors import NotFound
from config import CHAT_HISTORY
from config import CONVO_TIMEOUT
import time

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
async def end_inactive_chat(user_id, channel, active_threads, last_activity, timeout=CONVO_TIMEOUT):
    # Wait for the specified timeout
    await asyncio.sleep(timeout)

    # If the user is not in active_threads, do nothing
    if user_id not in active_threads:
        return

    try:
        # Check if the user has been inactive for the specified timeout
        last_activity_time = last_activity[user_id]
        current_time = time.time()
        inactivity_time = current_time - last_activity_time

        # If the user has been inactive for the specified timeout, delete the channel
        if inactivity_time >= timeout:
            await channel.delete()
            # Remove the user from the active_threads set only after deleting the channel
            active_threads.discard(user_id)
            # Remove the user from the last_activity dictionary
            last_activity.pop(user_id, None)
        else:
            # Reschedule the check with the remaining time
            remaining_time = timeout - inactivity_time
            asyncio.create_task(end_inactive_chat(user_id, channel, active_threads, last_activity, remaining_time))
    except NotFound:
        print(f"Channel not found for user {user_id}. It may have been deleted by another process.")
    except Exception as e:
        print(f"Error occurred while deleting the channel for user {user_id}: {e}")


