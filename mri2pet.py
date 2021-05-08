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


def pre_process_mri(image, gamma_correction=False):

    if gamma_correction:
        gamma = 0.15
        invGamma = 1.0 / gamma

        table = np.array([((i / 255.0) ** invGamma) * 255
                          for i in np.arange(0, 256)]).astype("uint8")

        image = cv2.LUT(image, table).astype(np.uint8)

    return image


def read_nifti(file):
    #run("mkdir images")
    #run("med2image -i " + file + " -o /images/slice")

    convert(file, "./input/img/img")
    folder = "./input/img"
    files = sorted(listdir(folder))
    images = []

    print(bcolors.BOLD, len(files), bcolors.ENDC)

    for i in range(len(files)):
        data = cv2.imread(folder + '/' + files[i])
        print(data.shape)
        data = pre_process_mri(data, gamma_correction=True)
        images.append(data)

    images = np.asarray(images)

    '''
    filename = 'images.npz'
    savez_compressed(filename, images)
    '''
    # shutil.rmtree("images") #run("rm -rf images")
    return images


class Mri2Pet:

    def __init__(self, load_test_data=False):
        self.model = model()
        self.data = None

        if load_test_data:
            self.data = load_test()

    def load_test_data(self):
        self.data = load_test()

    def test(self, n=245, m=50):
        inp_images = self.data[0][n: n+m]
        output_img = self.predict(inp_images)
        output_nii = img_to_nii(output_img)

        nib.save(output_nii, path.join(
            THIS_FOLDER, 'output/nii/output.nii.gz'))

    def next(self, file):
        print(bcolors.OKBLUE + "Starting" + bcolors.ENDC)

        print(bcolors.OKBLUE + "Processing Data..." + bcolors.ENDC)
        inp_images = read_nifti(file)
        print(bcolors.OKBLUE + "Processing complete" + bcolors.ENDC)

        print(bcolors.OKBLUE + "Generating Pet..." + bcolors.ENDC)
        output_img = self.predict(inp_images)
        print(bcolors.OKBLUE + "Pet Generation complete" + bcolors.ENDC)

        print(bcolors.OKBLUE + "Saving .nii file of result..." + bcolors.ENDC)
        output_nii = img_to_nii(output_img)
        nib.save(output_nii, path.join(THIS_FOLDER, 'output/nii/pet.nii.gz'))
        print(bcolors.OKBLUE + "Completed" + bcolors.ENDC)

    def predict(self, inp_images):
        inp_images = (inp_images - 127.5) / 127.5
        fake_images = zeros(inp_images.shape)
        slice_no = 1

        for i in range(len(inp_images)):
            fake_images[i] = self.model.predict(inp_images[i:i+1])
            print("Slice number :", slice_no, "completed")
            slice_no += 1

        predicted_imgs = copy(fake_images)
        predicted_data = path.join(THIS_FOLDER, 'output', 'img')

        print(bcolors.OKCYAN + "Result shape :",
              predicted_imgs.shape, bcolors.ENDC)

        for i in range(len(inp_images)):
            plt.imsave(f"{predicted_data}/predict_{i}.jpeg",
                       normalize(predicted_imgs[i]), cmap=plt.cm.Greys_r)

        return predicted_imgs
