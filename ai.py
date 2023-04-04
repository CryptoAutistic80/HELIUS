import asyncio
import openai
from config import MAX_RETRIES

async def process_requests(request_queue, api_semaphore, prompt_parameters, user_chat_histories):
    while True:
        tasks = []
        for _ in range(api_semaphore._value):  # Get the available API slots
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

        try:
            await asyncio.wait_for(request_queue.join(), timeout=0.5)  # Short sleep to avoid excessive looping
        except asyncio.exceptions.TimeoutError:
            pass  # Ignore the timeout and continue the loop

async def get_response(message_author_id, message_content, api_semaphore, prompt_parameters, user_chat_histories):
    for attempt in range(MAX_RETRIES):
        try:
            async with api_semaphore:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, lambda: openai.ChatCompletion.create(
                    model=prompt_parameters["model"],
                    messages=prompt_parameters["messages"] + user_chat_histories.get(message_author_id, []) + [{"role": "user", "content": message_content}],
                    max_tokens=200
                ))
            return response.choices[0].message['content'].strip()
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"Error occurred while processing message. Retry attempt {attempt + 1}: {e}")
                await asyncio.sleep(1)
            else:
                raise e
