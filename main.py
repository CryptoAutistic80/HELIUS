import discord
import asyncio
from discord.ext import commands
from discord.errors import NotFound
from keep_alive import keep_alive
from config import OPENAI_KEY
from config import TOKEN
from utils import load_prompt_parameters, add_chat_history
from ai import openai
from ai import process_requests

openai.api_key = OPENAI_KEY

intents = discord.Intents.all()
client = commands.Bot(command_prefix="!", intents=intents)

active_threads = set()

user_chat_histories = {}

prompt_parameters = load_prompt_parameters('prompt_parameters.json')

api_semaphore = asyncio.Semaphore(30)

# Create the request queue
request_queue = asyncio.Queue()

@client.event
async def on_ready():
    print('We have logged in as {0.user} in main'.format(client))
    asyncio.create_task(process_requests(request_queue, api_semaphore, prompt_parameters, user_chat_histories))

@client.command()
async def chat(ctx):
    if ctx.author.id in active_threads:
        await ctx.send("Woooah easy tiger! One conversation not enough for you?")
    else:
        print("Chat command triggered")
        thread = await ctx.channel.create_thread(name=f"Chat with {ctx.author.name}", type=discord.ChannelType.private_thread)
        await thread.send(f"Hello {ctx.author.mention}! You can start chatting with me. Type '!end' to end the conversation.")
        active_threads.add(ctx.author.id)

@client.command()
async def end(ctx):
    if isinstance(ctx.channel, discord.Thread) and ctx.channel.is_private:
        await asyncio.sleep(2)
        await ctx.channel.delete()
        active_threads.discard(ctx.author.id)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Process commands first
    await client.process_commands(message)

    # Ignore messages in non-private threads or outside threads
    if not isinstance(message.channel, discord.Thread) or not message.channel.is_private:
        return

    # Check message length
    if len(message.content.split()) > 80:
        await message.channel.send("As much as I like you, I ain't your personal proof reader.....keep in under 80 words please.")
        return

    add_chat_history(message.author.id, message.author, message.content, user_chat_histories)

    message_content = message.content
    response_future = asyncio.Future()

    await request_queue.put((message.author.id, message_content, response_future))

    try:
        async with message.channel.typing():
            response_text = await response_future
        if message.channel:
            await message.channel.send(response_text)
            add_chat_history(message.author.id, client.user, response_text, user_chat_histories)
    except NotFound:
        pass
    except Exception as e:
        print(f"Error occurred while processing message after all retries: {e}")
        await message.channel.send("I'm sorry, there was an issue processing your request. Please try again later.")

keep_alive()
client.run(TOKEN)