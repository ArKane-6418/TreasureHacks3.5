from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route('/')
def index():
    return render_template("index.html")

@app.route("/", methods=["GET", "POST"])
def upload_image():
    if request.method == "POST":
        # Get the uploaded image
        img_file = request.files["image"]

        # Pass image to model code to return deep dream version
        return render_template("index.html", img=img_file)
    return "success"

if __name__ == "__main__":
    app.run(debug=True)