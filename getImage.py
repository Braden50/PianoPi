import sys
import os
from google_images_download import google_images_download
from PIL import Image
import numpy as np


def main(query):
    paths = download(query)[0][query]
    print(paths)
    analyzeImage(paths[0])


def download(query):
    response = google_images_download.googleimagesdownload()
    arguments = {
        "keywords":query,
        "limit":5,
        "format": 'jpg',
        'output_directory':'images',
        'silent_mode': True,
    }
    paths = response.download(arguments)
    return paths


def analyzeImage(image_path):
    img = np.asarray(Image.open(image_path))
    r = img[:,:,0]
    #Image.fromarray(r).save("red.jpg")
    g = img[:,:,1]
    b = img[:,:,2]
    
    img_info = {
        'r': {
            'med': np.median(r),
            'std': np.std(r)
            },
        'g': {
            'med': np.median(g),
            'std': np.std(g)
            },
        'b': {
            'med': np.median(b),
            'std': np.std(b)
            },
        }
    return img_info


def getWaveInfo(query):
    paths = download(query)[0][query]
    img_info = analyzeImage(paths[0])
    print(img_info)
    s = 1
    config = {
            'r': {
                'min':img_info['r']['med'] - s * img_info['r']['std'],
                'max':img_info['r']['med'] + s * img_info['r']['std'],
                'period': 5,
                'offset':0
                },
            'g': {
                'min':img_info['g']['med'] - s * img_info['g']['std'],
                'max':img_info['g']['med'] + s * img_info['g']['std'],
                'period': 5,
                'offset':0
                },
            'b': {
                'min':img_info['b']['med'] - s * img_info['b']['std'],
                'max':img_info['b']['med'] + s * img_info['b']['std'],
                'period': 5,
                'offset':0
                },
            }
    for path in paths:
        os.remove(path)
    return config



if __name__=="__main__":
    if len(sys.argv) < 2:
        raise Exception("Usage: 'python file.py <query>")
    main(sys.argv[1])

#print complete paths to the downloaded images