from keras.models import load_model
import nibabel as nib
from numpy import load, zeros, copy, arange, eye
from os import path
import cv2
from os import listdir
from os import system as run
import numpy as np
#from numpy import savez_compressed
from med2img.med2img import convert
from matplotlib import pyplot as plt
import shutil
import gzip


DATA = "input"

SHELL = "shell_scripts"

# Temp
SKULL_STRIP = f'{DATA}/temp/skull_strip'
DENOISE = f'{DATA}/temp/denoise'
BAIS_COR = f'{DATA}/temp/bias_cor'
TEMP_OUTPUT = f'{DATA}/temp/output'


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


THIS_FOLDER = path.dirname(path.abspath(__file__))


def normalize(x):
    return np.array((x - np.min(x)) / (np.max(x) - np.min(x)))


def img_to_nii(img):
    res = np.zeros(img.shape[:-1])

    for i in range(img.shape[0]):
        res[i] = cv2.flip(cv2.cvtColor(
            np.float32(img[i]), cv2.COLOR_BGR2GRAY), 0)

    return nib.Nifti1Image(res.T, affine=None)


def load_test():
    processed_data = path.join(
        THIS_FOLDER, 'model/gamma_corrected_test_data.npz')
    dataset = load_real_samples(processed_data)
    print(bcolors.UNDERLINE + "Input :",
          dataset[0].shape, "Output :", dataset[1].shape, bcolors.ENDC)
    image_shape = dataset[0].shape[1:]
    [X1, X2] = dataset
    return [X1, X2]


def model():
    g_model_file = path.join(THIS_FOLDER, 'model/g_model_ep_000035.h5')
    generator = load_model(g_model_file)
    return generator


def load_real_samples(filename):
    data = load(filename)
    X1, X2 = data['arr_0'], data['arr_1']
    X1 = (X1 - 127.5) / 127.5
    X2 = (X2 - 127.5) / 127.5
    return [X1, X2]


def gamma_correction(image):
    gamma = 0.15
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255
                      for i in np.arange(0, 256)]).astype("uint8")
    image = cv2.LUT(image, table).astype(np.uint8)
    return image


def read_nifti(file):
    convert(file, "./input/img/img")
    folder = "./input/img"
    files = sorted(listdir(folder))
    images = []

    # input/img/img-slice000.png

    print(bcolors.BOLD, len(files), bcolors.ENDC)

    for i in range(len(files)):
        data = cv2.imread(folder + '/' + files[i])
        print(data.shape)
        data = gamma_correction(data)
        padded_input = pad_2d(data, 256, 256)
        images.append(padded_input)

    images = np.asarray(images)
    return images


def upzip_gz(input, output):
    with gzip.open(input, 'rb') as f_in:
        with open(output, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


def exception_handle(log_name):
    with open(f"./logs/{log_name}", "r") as log:
        status = log.read().strip()
        if(status == "failed"):
            print(f"\n{log_name} FAILED\n")
            return False
        print(f"\n{log_name} PASSED\n")
        return True


def intensity_normalization(input_image, output_image):
    print("\nDENOISING\n")
    # print("\ninput image: "+ input_image)
    # print("\noutput image: "+ output_image)
    log_name = "DENOISING"
    run(
        f"bash {SHELL}/denoise.sh {input_image} {output_image} {log_name}")
    return exception_handle(log_name)


def skull_strip(input_image):
    scan = input_image.split("/")[-1][:-4]
    print("\nSKULL STRIPPING\n")
    # print("\ninput image: "+ input_image)
    # print("\noutput image: "+ f"{SKULL_STRIP}/{scan}_sk.nii")
    log_name = "SKULL_STRIPPING"
    run(
        f"bash {SHELL}/skull_strip.sh {input_image} {SKULL_STRIP} {log_name}")
    upzip_gz(f"{SKULL_STRIP}/{scan}_masked.nii.gz",
             f"{SKULL_STRIP}/{scan}_sk.nii")
    return exception_handle(log_name)


def bias_correction(input_image, output_image):
    print("\nBIAS CORRECTION\n")
    # print("\ninput image: "+ input_image)
    # print("\noutput image: "+ output_image)
    log_name = "BIAS_CORRECTION"
    run(f"bash {SHELL}/bias.sh {input_image} {output_image} {log_name}")
    return exception_handle(log_name)


def preprocess(input, Skull_Strip=True, Denoise=True, Bais_Correction=True):
    print("\n-------------------MRI PREPROCESS STARTED--------------------\n")
    if(Denoise):
        if(intensity_normalization(input, f"{DENOISE}/mri")):
            input = f"{DENOISE}/mri.nii"
        else:
            return False
    if(Skull_Strip):
        if(skull_strip(input)):
            input = f"{SKULL_STRIP}/mri_sk.nii"
        else:
            return False
    if(Bais_Correction):
        if(bias_correction(input, f"{BAIS_COR}/mri.nii")):
            input = f"{BAIS_COR}/mri.nii"
        else:
            return False
    shutil.copyfile(input, f"{TEMP_OUTPUT}/mri.nii")
    print("\nTemp mri image: " + f"{TEMP_OUTPUT}/mri.nii")
    print("\n-------------------MRI PREPROCESS COMPELETED--------------------\n")
    return True


def pad_2d(data, r, c):
    m, n, other = data.shape
    res = np.zeros((r, c, other))
    res[(r - m) // 2: (r - m) // 2 + m, (c - n) // 2: (c - n) // 2 + n, :] = data
    return res


def crop_2d(data, r, c):
    m, n = data.shape
    return data[(m - r) // 2: (m - r) // 2 + r, (n - c) // 2: (n - c) // 2+c]
