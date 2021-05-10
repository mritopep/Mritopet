from flask import Flask, render_template, request, redirect, url_for,  session
from mri2pet import Mri2Pet
from os import path, mkdir, listdir, unlink
from flask_ngrok import run_with_ngrok
from werkzeug.utils import secure_filename
from shutil import rmtree
import time
import string
import random

from server_util import *

app_root = path.dirname(path.abspath(__file__))

app = Flask(__name__)

app.secret_key = generate_secret_key()

run_with_ngrok(app)

model = Mri2Pet()

print(bcolors.BOLD, model, bcolors.ENDC, flush=True)

@app.route("/")
def index():
    # initialization
    if 'start' not in session: 
        session['skull_strip'] = False
        session['denoise'] = False
        session['bias_field_correction'] = False
        session['file_upload_start'] = False
        session['file_upload_end'] = False
        session['process_start'] = False
        session['process_end'] = False
        session['generate_start'] = False
        session['generate_end'] = False
        session['saving_start'] = False
        session['saving_end'] = False
        session['start'] = True
        session['end'] = False
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


@app.route("/next", methods=['GET', 'POST'])
def next():
    global model

    start_time = time.time()

    print(bcolors.OKBLUE + "Starting" + bcolors.ENDC)

    input_folder = path.join(app_root, 'input', 'nii')
    file_path = input_folder + '/' + listdir(input_folder)[0]

    print(f"File path : {file_path}")

    session['process_start'] = True

    session['skull_strip'] = True
    session['denoise'] = True
    session['bias_field_correction'] = True

    session['process_end'] = model.process(
        file_path, Skull_Strip=session['skull_strip'], Denoise=session['denoise'], Bais_Correction=session['bias_field_correction'])

    if(session['process_end'] == False):
        session['process_start'] = False
        session['process_end'] = False
        print(bcolors.FAIL+"Process failed restart process with change in configuration"+bcolors.ENDC)
    else:
        session['generate_start']  = True

        model.generate()

        session['generate_end'] = True

        session['saving_start'] = True

        model.save()

        session['saving_end'] = True

        print(bcolors.OKGREEN + 'Pet saved' + bcolors.ENDC)

        session['start'] = False
        session['end'] = True

    end_time = time.time()
    print(bcolors.OKCYAN+f"Time Taken : {(end_time-start_time)/60} min"+bcolors.ENDC)

    return redirect(url_for('index'))


@app.route("/download", methods=['GET', 'POST'])
def download():
    file_path = path.join(app_root, 'output/nii/pet.nii.gz')

    def generate():
        with open(file_path, "rb") as file:
            yield from file

        delete_contents('./output')
        delete_contents('./input')

        session['skull_strip'] = False
        session['denoise'] = False
        session['bias_field_correction'] = False
        session['file_upload_start'] = False
        session['file_upload_end'] = False
        session['process_start'] = False
        session['process_end'] = False
        session['generate_start'] = False
        session['generate_end'] = False
        session['saving_start'] = False
        session['saving_end'] = False
        session['start'] = True
        session['end'] = False

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
