from flask import Flask, request, render_template
from chatjesset import run

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form["query"]
        try:
            result = run(query)
        except Exception as e:
            result = f"Whoops something didn't quite work! Perhaps too many people are trying to ask me questions at the moment. Please try again later."
        return render_template("index.html", result=result, query=query)
    else:
        return render_template("index.html")


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
