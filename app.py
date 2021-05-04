from flask import Flask, render_template, request, send_file,redirect
from mri2pet import Mri2Pet
from os import path,mkdir
from flask_ngrok import run_with_ngrok
from werkzeug.utils import secure_filename

app_root = path.dirname(path.abspath(__file__))

app = Flask(__name__,
            static_url_path='', 
            static_folder='./static',
            template_folder='./templates')

run_with_ngrok(app)

model = Mri2Pet()
print(model,flush=True)

@app.route("/", methods=['GET', 'POST'])
def index():
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
    global model
    model.test()
    return render_template("index.html")

@app.route("/download", methods=['GET', 'POST'])
def download():
    download = path.join(app_root, 'output/nii/pet.nii.gz')
    return send_file(download, as_attachment=True)


def create_folders():
    input_folder = path.join(app_root, 'input')
    if not path.exists(input_folder):
        mkdir(input_folder)
        mkdir(path.join(input_folder,"nii"))
        mkdir(path.join(input_folder,"img"))

    output_folder = path.join(app_root, 'output')
    if not path.exists(output_folder):
        mkdir(output_folder)
        mkdir(path.join(output_folder,"nii"))
        mkdir(path.join(output_folder,"img"))

def supported_file(filename):
    if "." not in filename:
        return False
    ext=filename.rsplit(".",1)[1]
    if ext=="nii":
        return True
    else:
        return False

@app.route("/upload", methods=['GET', 'POST'])
def upload():
    global model
    if request.method == 'POST':
        if request.files:
            f = request.files['mri_file']
            if not supported_file(f.filename):
                print("File not supported")
                return redirect(request.url)
            else:
                create_folders()
                filename=secure_filename(f.filename)
                f.save(path.join(app_root,'input','nii',filename))
                print("uploaded")
                #model.next(path.join(app_root,'input','nii',filename))
                #print('Pet saved')

            return redirect(request.url)
            #'file uploaded successfully'
    return render_template("index.html")

if __name__ == '__main__':
    app.run()