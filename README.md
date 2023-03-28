# ChatJesseT

## Usage

`requirements_test.txt` contains the full python environment used for development and testing. `requirements.txt` contains the more minimal version for deploying the Flask app.

Set the OpenAI key (for embedding and chat completion calls):
```
export OPENAI_API_KEY="sk-xxx..."
```

Set a system prompt at `data/db/system_prompt.txt` and a context prompt at `data/db/context_prompt.txt`. The former will guide the general characteristics of the chatbot, while the later will give a stronger immediate signal.

To create text chunks and embeddings, run [`notebooks/01_data_collection.ipynb`](notebooks/01_data_collection.ipynb) and [`notebooks/02_embedding.ipynb`](notebooks/02_embedding.ipynb).

For local testing, simply do
```
python main.py
```
and navigate to `http://127.0.0.1:8080/`.

Deploy website through the Google App Engine with
```
gcloud app deploy
```
and navigate to the remote URL via
```
gcloud app browse
```
See [here](https://cloud.google.com/appengine/docs/standard/python3/runtime) for preliminary steps necessary for Google Cloud / App Engine deployment. For initing [Google Cloud](https://cloud.google.com/docs/authentication/provide-credentials-adc#how-to).

To upload the text chunks and embeddings to Google Cloud, do this manually [here](https://console.cloud.google.com/storage/browser/chatjesset.appspot.com)

## TODO

- [ ] Fix parsing issues from personal website scrape
- [ ] Decrease embedding size and stride
- [ ] Increase number of relevant blocks used for context
- [ ] Set up a DB/streaming approach to cache text and embeddings db
- [ ] Estimate costs and plan deployment accordingly
- [ ] Make config store