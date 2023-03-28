import os
import pandas as pd
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import csv
from google.cloud import storage
import io
from utils.embedding_utils import get_embedding

n_relevant_chunks = 3

openai.api_key = os.environ.get("OPENAI_API_KEY")
storage_client = storage.Client()

with open("./data/db/system_prompt.txt") as f:
    """Load system prompt."""
    system_prompt = " ".join(line.rstrip() for line in f)

with open("./data/db/context_prompt.txt") as f:
    context_prompt = " ".join(line.rstrip() for line in f)


def semantic_search(query_embedding, embeddings):
    """Load context prompt."""
    similarities = cosine_similarity([query_embedding], embeddings)[0]
    ranked_indices = np.argsort(-similarities)
    return ranked_indices


def answer_question(chunk, question, model="gpt-3.5-turbo", max_tokens=300, temperature=0.7):
    prompt = f"Use the following pieces of context to answer the question at the end: {chunk}\nQuestion: {question}. {context_prompt}. \nAnswer:"
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        n=1,
        temperature=temperature,
    )
    return response["choices"][0]["message"]["content"]


def load_csv_file_from_gcs(bucket_name, file_name):
    gcs_path = f"gs://{bucket_name}/{file_name}"
    return pd.read_csv(gcs_path)


def load_npy_file_from_gcs(bucket_name, file_name):
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)
    npy_string = blob.download_as_bytes()
    npy_file = io.BytesIO(npy_string)
    return np.load(npy_file)


def run(query):
    if not query:
        return "Please enter your question above, and I'll do my best to help you."
    if len(query) > 150:
        return "Please ask a shorter question!"
    else:
        df_text = load_csv_file_from_gcs("chatjesset.appspot.com", "text_chunks.csv")
        embeddings = load_npy_file_from_gcs("chatjesset.appspot.com", "embeddings.npy")
        query_embedding = get_embedding(query)
        ranked_indices = semantic_search(np.array(query_embedding), embeddings)
        most_relevant_chunk = " ".join(df_text.loc[ranked_indices[:n_relevant_chunks], "text_chunks"].values.flatten())
        answer = answer_question(most_relevant_chunk, query)
        answer.strip("\n")
        return answer
