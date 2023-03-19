import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"

import openai
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

n_relevant_chunks = 3

df_emb = pd.read_csv("./data/db/text_chunks.csv")
embeddings = np.load("./data/db/embeddings.npy")

openai.api_key = os.environ.get("OPENAI_API_KEY")

with open("./data/db/system_prompt.txt") as f:
    system_prompt = " ".join(line.rstrip() for line in f)

with open("./data/db/context_prompt.txt") as f:
    context_prompt = " ".join(line.rstrip() for line in f)


def semantic_search(query_embedding, embeddings):
    similarities = cosine_similarity([query_embedding], embeddings)[0]
    ranked_indices = np.argsort(-similarities)
    return ranked_indices


def answer_question(chunk, question, model="gpt-3.5-turbo", max_tokens=300, temperature=0.7):
    question = f"Here is some information: {chunk}\nQuestion: {question}. {context_prompt}"
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": question}],
        max_tokens=max_tokens,
        n=1,
        temperature=temperature,
    )
    return response["choices"][0]["message"]["content"]


# def get_embedding(text, model="text-embedding-ada-002"):
#     text = text.replace("\n", " ")
#     return openai.Embedding.create(input=[text], model=model)["data"][0]["embedding"]


def get_embedding(text, model="all-MiniLM-L6-v2"):
    model = SentenceTransformer(model, device="cpu")
    return model.encode(text)


def run(query):
    query_embedding = get_embedding(query)
    ranked_indices = semantic_search(np.array(query_embedding), embeddings)
    most_relevant_chunk = " ".join(np.array(df_emb["text_chunks"])[ranked_indices[:n_relevant_chunks]].flatten())
    answer = answer_question(most_relevant_chunk, query)
    answer.strip("\n")
    return answer
