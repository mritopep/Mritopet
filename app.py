from flask import Flask, render_template, request, redirect, url_for,  session
from mri2pet import Mri2Pet
from os import path, mkdir, listdir, unlink
from flask_ngrok import run_with_ngrok
from werkzeug.utils import secure_filename
from shutil import rmtree
import time
import string
import random
from flask import Response
import shutil

from server_util import *
from model_util import *

app_root = path.dirname(path.abspath(__file__))

app = Flask(__name__,
            static_url_path='',
            static_folder='static',
            template_folder='templates')

app.secret_key = generate_secret_key()

run_with_ngrok(app)

model = Mri2Pet()

print(bcolors.BOLD, model, bcolors.ENDC, flush=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=['GET', 'POST'])
def upload():
    session['file_upload_start'] = True

    if request.method == 'POST':
        if request.files:
            f = request.files['mri_file']
            if not supported_file(f.filename):
                print("File not supported")
                return redirect(request.url)
            else:
                create_folders()
                filename = secure_filename(f.filename)
                f.save(path.join(app_root, 'input', 'nii', filename))
                print("uploaded")
                session['file_upload_end'] = True

    return redirect(url_for('index'))


def stream_template(template_name, **context):
    app.update_template_context(context)
    t = app.jinja_env.get_template(template_name)
    rv = t.stream(context)
    # rv.enable_buffering(5)
    return rv


@app.route("/next", methods=['GET', 'POST'])
def next():
    print(bcolors.OKBLUE + "Starting" + bcolors.ENDC)
    input_folder = path.join(app_root, 'input', 'nii')
    file_path = input_folder + '/' + listdir(input_folder)[0]
    print(f"File path : {file_path}")

    def process(model, file_path, Skull_Strip, Denoise, Bais_Correction):
        print("Inside Generator")
        boolean = []
        boolean.append("start")
        yield boolean
        boolean.append("process_start")
        yield boolean
        model.process(file_path, Skull_Strip=Skull_Strip,
                      Denoise=Denoise, Bais_Correction=Bais_Correction)
        boolean.append("process_end")
        yield boolean
        boolean.append("generate_start")
        yield boolean
        model.generate()
        boolean.append("generate_end")
        yield boolean
        boolean.append("saving_start")
        yield boolean
        model.save()
        boolean.append("saving_end")
        yield boolean
        boolean.append("end")
        boolean.remove("start")
        yield boolean
    return Response(stream_template('sample.html', 
    boolean=process(model, file_path, Skull_Strip=True, Denoise=True, Bais_Correction=True)))


@app.route("/download", methods=['GET', 'POST'])
def download():
    file_path = path.join(app_root, 'output/nii/pet.nii.gz')

    def generate():
        with open(file_path, "rb") as file:
            yield from file

        delete_contents('./output')
        delete_contents('./input')

        print(bcolors.OKBLUE + "All files deleted" + bcolors.ENDC)

    response = app.response_class(generate(), mimetype='application/x-gzip')
    response.headers.set('Content-Disposition',
                         'attachment', filename="pet.nii.gz")
    return response


@app.route("/test", methods=['GET', 'POST'])
def test():
    global model
    model.load_test_data()
    model.test()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
