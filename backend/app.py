from flask import Flask, request, send_file, make_response
from werkzeug.utils import secure_filename
import os
from haloopinate import haloopinate
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config["UPLOAD"] = os.path.join('static', 'uploads')

# @app.route('/')
# def index():
#     return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate_deep_dream():
        # if request.form["submit"] == "Submit":
        #     # Get the uploaded image
        #     file = request.files["image"]
        #     filename = secure_filename(file.filename)

        #     # Save image locally and get the path
        #     file.save(os.path.join(app.config['UPLOAD'], filename))
            
        #     img_path = os.path.join(app.config['UPLOAD'], filename)
        #     return render_template("index.html", img=img_path)
        
        # elif request.form['submit'] == 'Generate':
        # Pass image to model code to return deep dream version
    # print(request.content_length)
    file = request.files['image']
    filename = secure_filename(file.filename)

    # Save image locally and get the path
    file.save(os.path.join(app.config['UPLOAD'], filename))
    
    img_path = os.path.join(app.config['UPLOAD'], filename)
    export_path = os.path.join(app.config['UPLOAD'], filename + '_haloopinated.gif')
    haloopinate(image_path=img_path, export_path=export_path, duration=6, debug=True)
    response = make_response(send_file(export_path, mimetype='image/gif'))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
        
# @app.route("/generate", methods=["POST"])
# def generate_deep_dream():
#     print(request.method)
#     if request.method == "POST":
        
        

if __name__ == "__main__":
    app.run(debug=True)