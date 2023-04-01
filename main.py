from flask import Flask, request, render_template
from chatjesset import run
import logging

log_handler = logging.StreamHandler()
log_formatter = logging.Formatter("%(asctime)s - %(message)s")
log_handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

app = Flask(__name__)

api_key_mode = "system"  # "user"" or "system"
SHOW_API_KEY_BOX = True if api_key_mode == "user" else False


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form["query"]

        # Get answer or error message
        try:
            if api_key_mode == "user":
                api_key = request.form["api_key"].strip()
                if api_key == "":  # API key is not provided in user mode; show error
                    result = f"Please enter your OpenAI API Key!"
                elif api_key != "":  # If API key provided in user mode; use it
                    result = run(query, api_key=api_key)
            elif api_key_mode == "system":  # API key is not required in system mode; use system key
                api_key = None
                result = run(query, api_key=api_key)
                logger.info(f"User input: {query}")  # Using logger
            else:
                raise NotImplementedError("Please set api_key_mode to either 'user' or 'system'.")
        except Exception as e:
            result = f"Whoops something didn't quite work! Perhaps too many people are trying to ask me questions at the moment. Please try again later."
        return render_template("index.html", result=result, query=query, show_api_key_box=SHOW_API_KEY_BOX)
    else:
        return render_template("index.html", show_api_key_box=SHOW_API_KEY_BOX)


@app.route("/")
def home():
    return render_template("index.html", show_api_key_box=SHOW_API_KEY_BOX)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
