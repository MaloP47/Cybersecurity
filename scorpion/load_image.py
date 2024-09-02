# import numpy as np
from PIL import Image
import os


def channel(mode: str) -> int:
    """Return nb of channels for a given mode"""
    toChannel = {
        "1": 1,
        "L": 1,
        "P": 1,
        "RGB": 3,
        "RGBA": 4,
        "CMYK": 4,
        "YCbCr": 3,
        "LAB": 3,
    }
    return toChannel.get(mode, 0)


def ft_load(path: str) -> Image:
    """Load a .JPEG or .JPG, prints format and pixels in RGB"""

    if not isinstance(path, str):
        raise Exception("wrong type")
    if not os.path.isfile(path):
        raise Exception(f"invalid parameter : {path}")

    try:
        img = Image.open(path)
    except Exception:
        raise Exception("not supported")

    # norm = f'({img.size[1]}, {img.size[0]}, {channel(img.mode)})'
    # print(f'The shape of image is: {norm}')
    # pix = np.array(img)
    # img.close()
    # return pix
    return img
