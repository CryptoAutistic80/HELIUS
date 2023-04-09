# Import necessary libraries
import os
from utils import json
import asyncio
import openai
import pinecone
import numpy as np
from config import MAX_RETRIES, PINECONE_KEY
from document_processing import embed_text
from document_processing import output_path
from config import TOP_K_SIMILAR_DOCS

# Intialise pinecone
pinecone.init(api_key=PINECONE_KEY, environment='us-east1-gcp')
pinecone_indexer = pinecone.Index("core-69")

# Fuction to query pinecone
async def query_pinecone(query_vector_np, top_k=TOP_K_SIMILAR_DOCS, namespace="pdf-documents"):
    query_results = pinecone_indexer.query(
        vector=query_vector_np.tolist(),
        top_k=top_k,
        namespace=namespace,
    )
    metadata_list = []
    for match in query_results['matches']:
        uuid_val = match['id']
        with open(os.path.join(output_path, f'{uuid_val}.json'), 'r') as f:
            metadata = json.load(f)
        metadata_list.append(metadata)
    return metadata_list

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
            # Get the user's chat history
            chat_history = user_chat_histories.get(message_author_id, [])
            
            # Convert the user's message to an embedding
            message_embedding = np.array(embed_text(message_content), dtype=np.float32)
            
            # Query Pinecone for the top 4 semantically similar documents
            similar_docs_metadata = await query_pinecone(message_embedding)
            similar_text_metadata = [{"role": "assistant", "content": doc['text']} for doc in similar_docs_metadata]

            # Append the similar documents' metadata to the user's chat history
            chat_history_with_similar_docs = chat_history + similar_text_metadata + [{"role": "user", "content": message_content}]

            async with api_semaphore:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, lambda: openai.ChatCompletion.create(
                    model=prompt_parameters["model"],
                    messages=prompt_parameters["messages"] + chat_history_with_similar_docs,
                    max_tokens=500
                ))

            return response.choices[0].message['content'].strip()
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"Error occurred while processing message. Retry attempt {attempt + 1}: {e}")
                await asyncio.sleep(1)
            else:
                raise e








