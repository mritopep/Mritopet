
from keras.models import load_model
from PIL import Image
import nibabel as nib
from numpy import load, zeros, copy, arange, eye
from os import path
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

class Mri2Pet:

    def __init__(self):
        self.model = model()
        self.data = load_test()

    def test(self,n = 245,m = 120):
        inp_images = self.data[0][n : n+m]
        output_img = self.predict(inp_images)
        output_nii = img_to_nii(output_img)
        nib.save(output_nii, path.join(THIS_FOLDER, 'output/nii/output.nii.gz')) 

    def predict(self, inp_images):
        fake_images = zeros(inp_images.shape)
        for i in range(len(inp_images)):
        	fake_images[i] = self.model.predict(inp_images[i:i+1])
        predicted_imgs = copy(fake_images)
        predicted_data = path.join(THIS_FOLDER, 'output/img')
        for i in range(len(predicted_imgs)):
        	im = Image.fromarray((predicted_imgs[i] * 255).astype(np.uint8))
	        im.save(f"{predicted_data}/predict_{i}.jpeg")
        return predicted_imgs
        
        
