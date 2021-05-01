from flask import Flask, render_template, request, send_file
from mri2pet import Mri2Pet
from os import path
from flask_ngrok import run_with_ngrok

app_root = path.dirname(path.abspath(__file__))

app = Flask(__name__,
            static_url_path='', 
            static_folder='./static',
            template_folder='./templates')

run_with_ngrok(app)

model = Mri2Pet()

@app.route("/", methods=['GET', 'POST'])
def index():
    print(model,flush=True)
    if request.method == 'POST':
        # text = request.form['text']
        # print(text,flush=True)
        # emotion,confidence = emot.test(text)
        # print(emotion,confidence)
        return render_template("index.html")
    else:
        return render_template("index.html")

@app.route("/test", methods=['GET', 'POST'])
def test():
    model.test()

@app.route("/download", methods=['GET', 'POST'])
def download():
    download = path.join(app_root, 'output/nii/output.nii.gz')
    return send_file(download, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)