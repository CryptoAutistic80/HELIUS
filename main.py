# Import necessary libraries and modules
import discord
import asyncio
import threading
from discord.ext import commands
from discord.errors import NotFound
from keep_alive import keep_alive
from config import OPENAI_KEY
from config import TOKEN
from utils import load_prompt_parameters, add_chat_history
from ai import openai
from ai import process_requests
from utils import end_inactive_chat
from config import MESSAGE_WORD_LIMIT
from document_processing import process_all
import time

# Set OpenAI API key
openai.api_key = OPENAI_KEY

# Create a Bot instance with a custom command prefix and required intents
intents = discord.Intents.all()
client = commands.Bot(command_prefix="!", intents=intents)

# Initialize a set to store active threads (conversations)
active_threads = set()

# Initialize a dictionary to store last activity for each user
last_activity = {}

# Initialize a dictionary to store chat histories for each user
user_chat_histories = {}

# Load prompt parameters for OpenAI API requests
prompt_parameters = load_prompt_parameters('prompt_parameters.json')

# Create a Semaphore to limit the number of simultaneous API requests
api_semaphore = asyncio.Semaphore(30)

# Create the request queue for OpenAI API requests
request_queue = asyncio.Queue()

# Define the "on_ready" event that triggers when the bot logs in
@client.event
async def on_ready():
    print('We have logged in as {0.user} in main'.format(client))
    asyncio.create_task(process_requests(request_queue, api_semaphore, prompt_parameters, user_chat_histories))

# Define the "!chat" command to start a chat with the bot in a private thread
@client.command()
async def chat(ctx):
    if ctx.author.id in active_threads:
        await ctx.send("Woooah easy tiger! One conversation not enough for you?")
    else:
        print("Chat command triggered")

        # Check if the ctx.channel is a TextChannel before creating a thread
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.send("You can only start a chat in a text channel.")
            return

        thread = await ctx.channel.create_thread(name=f"Chat with {ctx.author.name}", type=discord.ChannelType.private_thread)
        await thread.send(f"Hello {ctx.author.mention}! You can start chatting with me. Type da command '!end' to wrap things up.....")
        active_threads.add(ctx.author.id)

        # Call end_inactive_chat after starting the conversation and pass the last_activity dictionary
        asyncio.create_task(end_inactive_chat(ctx.author.id, thread, active_threads, last_activity))

# Define the "!end" command to end a chat and delete the private thread
@client.command()
async def end(ctx):
    if isinstance(ctx.channel, discord.Thread) and ctx.channel.is_private:
        await asyncio.sleep(2)
        await ctx.channel.delete()
        active_threads.discard(ctx.author.id)

# Define the "on_message" event to handle messages and generate chatbot responses
@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == client.user:
        return

    # Update the user's last activity timestamp
    last_activity[message.author.id] = time.time()

    # Process commands first
    await client.process_commands(message)

    # Ignore messages in non-private threads or outside threads
    if not isinstance(message.channel, discord.Thread) or not message.channel.is_private:
        return

        # Check message length
    if len(message.content.split()) > MESSAGE_WORD_LIMIT:
        await message.channel.send(f"As much as I like you, I ain't your personal proof reader.....keep it under {MESSAGE_WORD_LIMIT} words please.")
        return

    # Add user message to chat history
    add_chat_history(message.author.id, message.author, message.content, user_chat_histories)

    # Prepare message content for OpenAI API request
    message_content = message.content
    response_future = asyncio.Future()

    # Add the request to the request_queue to be processed by the OpenAI API
    await request_queue.put((message.author.id, message_content, response_future))

    try:
        # Show "typing" status while waiting for the response
        async with message.channel.typing():
            response_text = await response_future
        # If the channel still exists, send the response
        if message.channel:
            await message.channel.send(response_text)
            # Add bot response to chat history
            add_chat_history(message.author.id, client.user, response_text, user_chat_histories)
    except NotFound:
        pass
    except Exception as e:
        print(f"Error occurred while processing message after all retries: {e}")
        await message.channel.send("I'm sorry, there was an issue processing your request. Please try again later.")

if __name__ == "__main__":
    # Create a Thread object and target it to the function you want to run in a separate thread
    process_thread = threading.Thread(target=process_all)

    # Start the thread
    process_thread.start()

    # Optional: If you want the main thread to wait until process_thread is done, uncomment the next line
    # process_thread.join()

    print("Document processing started successfully.")

    keep_alive()
    client.run(TOKEN)
    

