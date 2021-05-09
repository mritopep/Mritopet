from flask import Flask, render_template, request, redirect, url_for
from mri2pet import Mri2Pet
from os import path, mkdir, listdir, unlink
from flask_ngrok import run_with_ngrok
from werkzeug.utils import secure_filename
from shutil import rmtree


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


app_root = path.dirname(path.abspath(__file__))

app = Flask(__name__,
            static_url_path='',
            static_folder='./static',
            template_folder='./templates')

run_with_ngrok(app)

model = Mri2Pet()
print(bcolors.BOLD, model, bcolors.ENDC, flush=True)


def delete_contents(folder_path):
    folder = folder_path
    for filename in listdir(folder):
        file_path = path.join(folder, filename)
        try:
            if path.isfile(file_path) or path.islink(file_path):
                unlink(file_path)
            elif path.isdir(file_path):
                rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s : %s' % (file_path, e))

    rmtree(folder)


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
    model.load_test_data()
    model.test()
    return render_template("index.html")


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


def create_folders():
    input_folder = path.join(app_root, 'input')
    if not path.exists(input_folder):
        mkdir(input_folder)
        mkdir(path.join(input_folder, "nii"))
        mkdir(path.join(input_folder, "img"))

    output_folder = path.join(app_root, 'output')
    if not path.exists(output_folder):
        mkdir(output_folder)
        mkdir(path.join(output_folder, "nii"))
        mkdir(path.join(output_folder, "img"))


def supported_file(filename):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1]
    if ext == "nii":
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
                filename = secure_filename(f.filename)
                f.save(path.join(app_root, 'input', 'nii', filename))
                print("uploaded")
                return redirect(url_for('next'))

    return render_template("index.html")


@app.route("/next", methods=['GET', 'POST'])
def next():
    input_folder = path.join(app_root, 'input', 'nii')
    model.next(input_folder + '/' + listdir(input_folder)[0])
    print(bcolors.OKGREEN + 'Pet saved' + bcolors.ENDC)

    return redirect(url_for('download'))


if __name__ == '__main__':
    app.run()
