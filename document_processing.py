import os
import json
import re
import glob
import PyPDF2
import spacy
import nltk
import uuid
import openai
import pinecone
import numpy as np
from config import OPENAI_KEY, PINECONE_KEY

nltk.download('punkt')

pdf_path = 'Doc_Processing/PDF_documents/'
output_path = 'Doc_Processing/embeddings/'

if not os.path.exists(output_path):
    os.makedirs(output_path)

processed_docs_path = os.path.join('Doc_Processing')
if not os.path.exists(processed_docs_path):
    os.makedirs(processed_docs_path)

nlp = spacy.load('en_core_web_sm')

def embed_text(text):
    content = text.encode(encoding='ASCII', errors='ignore').decode()  # fix any UNICODE errors
    openai.api_key = OPENAI_KEY
    response = openai.Embedding.create(
        input=content,
        engine='text-embedding-ada-002'
    )
    vector = response['data'][0]['embedding']  # this is a normal list
    return vector

def extract_text(pdf_path):
    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        pages = []
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            pages.append({'page_num': page_num+1, 'text': page.extract_text()})
        return pages

def split_text(text):
    sentences = nltk.sent_tokenize(text)
    return ['\n'.join(sentences[i:i+8]) for i in range(0, len(sentences), 8)]

def clean_text(text):
    # Remove unwanted Unicode characters (e.g., \u2022)
    text = text.encode('ascii', errors='ignore').decode('ascii')
    # Replace newline characters with spaces
    text = text.replace('\n', ' ')
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def process_file(file):
    pages = extract_text(file)

    embeddings = []
    for page in pages:
        page_num = page['page_num']
        text = page['text']
        page_groups = split_text(text)
        for i, group in enumerate(page_groups):
            output_uuid = uuid.uuid4()
            output_filename = os.path.join(output_path, f'{output_uuid}.json')
            cleaned_text = clean_text(group)
            metadata = {'filename': os.path.basename(file), 'file_number': i+1, 'page_number': page_num, 'uuid': str(output_uuid), 'text': cleaned_text}
            vector = embed_text(cleaned_text)
            vector_np = np.array(vector)  # Convert the list to a NumPy array
            embeddings.append((metadata['uuid'], vector_np))

            # Save the metadata and cleaned text to a JSON file
            with open(output_filename, 'w') as f:
                json.dump(metadata, f, indent=4)

    # Upsert embeddings to Pinecone in smaller batches
    batch_size = 100
    pinecone.init(api_key=PINECONE_KEY, environment='us-east1-gcp')
    pinecone_indexer = pinecone.Index("core-69")
    for i in range(0, len(embeddings), batch_size):
        batch = embeddings[i:i + batch_size]
        pinecone_indexer.upsert([(unique_id, vector_np.tolist()) for unique_id, vector_np in batch], namespace="pdf-documents")


def process_files():
    processed_files = []
    processed_files_filename = os.path.join(processed_docs_path, 'processed_files.json')
    if os.path.exists(processed_files_filename):
        with open(processed_files_filename, 'r') as f:
            processed_files = json.load(f)

    for file in [file for file in glob.glob(os.path.join(pdf_path, '*.pdf')) if os.path.basename(file) not in processed_files]:
        process_file(file)

        # Add the processed file to the list of processed files
        processed_files.append(os.path.basename(file))

        # Save the list of processed files
        with open(processed_files_filename, 'w') as f:
            json.dump(processed_files, f, indent=4)

process_files()