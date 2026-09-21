"""Rebuild the text chunk / embedding database from the source documents.

Papers are kept as-is from `data/db/df_text.csv`; interview and website documents are
re-read from `data/interviews/*.txt` and `data/website/*.txt`, so editing, adding, or
removing a text file there and re-running this script updates the database.
Embeddings of unchanged chunks are reused, so only new text is sent to the OpenAI API.

Usage (from the repo root, with OPENAI_API_KEY set):
    python -m utils.rebuild_db
"""

import glob
import os

import numpy as np
import pandas as pd
from tqdm import tqdm

from utils.embedding_utils import get_embedding, sliding_window

db_dir = "data/db"
text_dirs = {"interview": "data/interviews", "website": "data/website"}

window_size = 256  # Length of text chunks
stride = 192  # Stride of sliding window; have a bit of overlap
max_chunks = 80  # If text too long, truncate


def load_documents():
    """Papers from the existing dataframe, everything else from the text directories."""
    df = pd.read_csv(f"{db_dir}/df_text.csv")
    df = df[df["source_type"] == "paper"]
    rows = []
    for source_type, text_dir in text_dirs.items():
        for filename in sorted(glob.glob(f"{text_dir}/*.txt")):
            with open(filename, "r") as f:
                rows.append({"source_type": source_type, "text": f.read()})
    return pd.concat([df, pd.DataFrame(rows)], ignore_index=True)


def main():
    df = load_documents()

    # Cache of existing embeddings, keyed by chunk text
    cache = {}
    if os.path.exists(f"{db_dir}/text_chunks.csv"):
        old_chunks = pd.read_csv(f"{db_dir}/text_chunks.csv")["text_chunks"].tolist()
        old_embeddings = np.load(f"{db_dir}/embeddings.npy")
        cache = dict(zip(old_chunks, old_embeddings))

    text_chunks = []
    for text in df["text"].values:
        text = text.replace("\n", " ").strip()
        text_chunks += list(sliding_window(text, window_size, stride))[:max_chunks]

    n_new = sum(chunk not in cache for chunk in text_chunks)
    print(f"{len(df)} documents, {len(text_chunks)} chunks, {n_new} to embed")

    embeddings = [
        cache[chunk] if chunk in cache else get_embedding(chunk)
        for chunk in tqdm(text_chunks)
    ]
    embeddings = np.array(embeddings, dtype=np.float64)

    df.to_csv(f"{db_dir}/df_text.csv", index=False)
    pd.DataFrame({"text_chunks": text_chunks}).to_csv(
        f"{db_dir}/text_chunks.csv", index=False
    )
    np.save(f"{db_dir}/embeddings.npy", embeddings)


if __name__ == "__main__":
    main()
