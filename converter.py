import torch
import cv2
import numpy as np
from PIL import Image
from diffusers import LDMSuperResolutionPipeline

from autoencoder.autoencoder import Autoencoder


class Mc2RealConverter:
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.autoencoder = Autoencoder.load_from_checkpoint(
            'autoencoder/checkpoints/checkpoint.ckpt',
            map_location=self.device
        )
        self.sr = LDMSuperResolutionPipeline.from_pretrained('CompVis/ldm-super-resolution-4x-openimages').to(self.device)

        self.last_downscaled = None
        self.last_realized = None
        self.last_blend = None
        self.last_upscaled = None

    def __call__(self, mc_img, blend_factor=0.5, sr_inference_steps=300):
        downscaled_img = self.__downscale(mc_img)
        self.last_downscaled = downscaled_img

        realized_img = self.__realize(downscaled_img)
        self.last_realized = realized_img

        blend_img = self.__blend(realized_img, downscaled_img, blend_factor)
        self.last_blend = blend_img

        upscaled_img = self.__upscale(blend_img, sr_inference_steps)
        self.last_upscaled = upscaled_img

        return upscaled_img

    def __downscale(self, img):
        return cv2.resize(img, (64, 64))

    def __realize(self, img):
        return self.autoencoder.predict(img)

    def __blend(self, img, mc_img, blend_factor):
        return blend_factor * mc_img + (1-blend_factor) * img

    def __upscale(self, img, inference_steps):
        pil_img = Image.fromarray((img*255).astype(np.uint8), 'RGB')
        large_img = self.sr(pil_img, num_inference_steps=inference_steps, eta=1).images[0]
        large_img = np.asarray(large_img, dtype=np.float32) / 255
        return large_img
