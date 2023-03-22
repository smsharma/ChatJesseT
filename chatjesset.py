import os

# os.environ["TOKENIZERS_PARALLELISM"] = "false"

import openai

# import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import csv

from utils.embedding_utils import get_embedding

n_relevant_chunks = 1

openai.api_key = os.environ.get("OPENAI_API_KEY")

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


def run(query):
    if not query:
        return "Please enter your question above, and I'll do my best to help you."
    if len(query) > 150:
        return "Please ask a shorter question!"
    else:
        with open("./data/db/text_chunks.csv") as csv_file:
            csv_reader = csv.reader(csv_file)
            embeddings = np.load("./data/db/embeddings.npy")

            query_embedding = get_embedding(query)
            ranked_indices = semantic_search(np.array(query_embedding), embeddings)
            most_relevant_chunk = ""
            for i, row in enumerate(csv_reader):
                if i in ranked_indices[:n_relevant_chunks]:
                    most_relevant_chunk += " ".join(row)

            answer = answer_question(most_relevant_chunk, query)
            answer.strip("\n")
            return answer
