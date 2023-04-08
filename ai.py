# Import necessary libraries
import asyncio
import openai
from config import MAX_RETRIES

# Function to process requests in the request queue
async def process_requests(request_queue, api_semaphore, prompt_parameters, user_chat_histories):
    while True:
        tasks = []
        # Iterate through available API slots
        for _ in range(api_semaphore._value):
            # If the request queue is not empty, get the request and create a task
            if not request_queue.empty():
                user_id, message_content, response_future = await request_queue.get()
                task = asyncio.create_task(get_response(user_id, message_content, api_semaphore, prompt_parameters, user_chat_histories))
                tasks.append((task, response_future))
                request_queue.task_done()
            else:
                break

        if tasks:
            # Use asyncio.gather() to process tasks concurrently
            results = await asyncio.gather(*(task for task, _ in tasks), return_exceptions=True)

            # Set the result or exception in the respective response_future
            for (task, response_future), result in zip(tasks, results):
                if isinstance(result, Exception):
                    response_future.set_exception(result)
                else:
                    response_future.set_result(result)

        # Short sleep to avoid excessive looping
        try:
            await asyncio.wait_for(request_queue.join(), timeout=0.5)
        except asyncio.exceptions.TimeoutError:
            pass  # Ignore the timeout and continue the loop

# Function to send the user message to OpenAI API and get the AI response
async def get_response(message_author_id, message_content, api_semaphore, prompt_parameters, user_chat_histories):
    for attempt in range(MAX_RETRIES):
        try:
            # Limit the number of concurrent API requests using the semaphore
            async with api_semaphore:
                loop = asyncio.get_event_loop()
                # Send the request to the OpenAI API
                response = await loop.run_in_executor(None, lambda: openai.ChatCompletion.create(
                    model=prompt_parameters["model"],
                    messages=prompt_parameters["messages"] + user_chat_histories.get(message_author_id, []) + [{"role": "user", "content": message_content}],
                    max_tokens=200
                ))
            # Return the AI-generated response
            return response.choices[0].message['content'].strip()
        except Exception as e:
            # Retry the request if it fails, up to MAX_RETRIES times
            if attempt < MAX_RETRIES - 1:
                print(f"Error occurred while processing message. Retry attempt {attempt + 1}: {e}")
                await asyncio.sleep(1)
            else:
                raise e
