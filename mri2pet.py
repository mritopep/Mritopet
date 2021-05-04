from keras.models import load_model
from PIL import Image
import nibabel as nib
from numpy import load, zeros, copy, arange, eye, uint8
from os import path
import cv2
from os import listdir
from os import system as run
import numpy as np
from numpy import savez_compressed
from med2img.med2img import convert
import shutil

THIS_FOLDER = path.dirname(path.abspath(__file__))

def load_test():
    processed_data = path.join(THIS_FOLDER, 'model/gamma_corrected_test_data.npz')
    dataset = load_real_samples(processed_data)
    print("Input :",dataset[0].shape, "Output :",dataset[1].shape)
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

def img_to_nii(img):
    # data = arange(4*4*3).reshape(4,4,3)
    image = nib.Nifti1Image(img, affine=eye(4))
    return image
    
def pre_process_mri(image, gamma_correction=False):

    if gamma_correction:
        gamma = 0.15
        invGamma = 1.0 / gamma

        table = np.array([((i / 255.0) ** invGamma) * 255
                          for i in np.arange(0, 256)]).astype("uint8")

        image = cv2.LUT(image, table).astype(np.uint8)

    return image


# file name should be having .nii
def save_to_npz(file, des = ""):
    #run("mkdir images")
    #run("med2image -i " + file + " -o /images/slice")
    convert(file,"./input/img/img")
    folder = "./input/img"
    files = sorted(listdir(folder))
    print(len(files))
    list = []
    for i in range(len(files)):
        data = cv2.imread(folder + '/' + files[i])
        data = pre_process_mri(data, gamma_correction=True)
        list.append(data)
    list = np.asarray(list)
    
    if des != "" : des += "/"
    filename = des + 'images.npz'
    savez_compressed(filename, list)
    
    #shutil.rmtree("images") #run("rm -rf images")
    return list

class Mri2Pet:

    def __init__(self):
        self.model = model()
        self.data = load_test()

    def test(self,n = 245,m = 50):
        inp_images = self.data[0][n : n+m]
        output_img = self.predict(inp_images)
        output_nii = img_to_nii(output_img)
        nib.save(output_nii, path.join(THIS_FOLDER, 'output/nii/output.nii.gz')) 
    
    def next(self,file):
        inp_images = save_to_npz(file)
        output_img = self.predict(inp_images)
        output_nii = img_to_nii(output_img)
        nib.save(output_nii, path.join(THIS_FOLDER, 'output/nii/pet.nii.gz'))


    def predict(self, inp_images):
        fake_images = zeros(inp_images.shape)
        for i in range(len(inp_images)):
        	fake_images[i] = self.model.predict(inp_images[i:i+1])
        predicted_imgs = copy(fake_images)
        predicted_data = path.join(THIS_FOLDER, 'output','img')
        print(len(predicted_imgs))
        for i in range(len(inp_images)):
            img = predicted_imgs[i]
            im = Image.fromarray((img * 255).astype(uint8))
            im.save(f"{predicted_data}/predict_{i}.jpeg")
        return predicted_imgs
        
