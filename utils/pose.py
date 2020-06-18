import numpy as np


def get_orientation(jsx, jdx):
    """
    given the foot joints checks the sight direction of the person
    @param jsx: left foot
    @param jdx: right foot
    @return: returns a string representing the direction "south-east" or "south-west"
    """
    _, y1 = jsx
    _, y2 = jdx

    # (0;0) is the top left corner of the image
    if all((y1, y2)):
        if y1 < y2:
            return "s_e"
        if y1 > y2:
            return "s_w"
        else:
            raise NotImplementedError
    else:
        raise Exception('One or both joints not found.')


def pad_right_down_corner(img, stride, pad_value):
    h = img.shape[0]
    w = img.shape[1]

    pad = 4 * [None]
    pad[0] = 0  # up
    pad[1] = 0  # left
    pad[2] = 0 if (h % stride == 0) else stride - (h % stride)  # down
    pad[3] = 0 if (w % stride == 0) else stride - (w % stride)  # right

    img_padded = img
    pad_up = np.tile(img_padded[0:1, :, :] * 0 + pad_value, (pad[0], 1, 1))
    img_padded = np.concatenate((pad_up, img_padded), axis=0)
    pad_left = np.tile(img_padded[:, 0:1, :] * 0 + pad_value, (1, pad[1], 1))
    img_padded = np.concatenate((pad_left, img_padded), axis=1)
    pad_down = np.tile(img_padded[-2:-1, :, :] * 0 + pad_value, (pad[2], 1, 1))
    img_padded = np.concatenate((img_padded, pad_down), axis=0)
    pad_right = np.tile(img_padded[:, -2:-1, :] * 0 + pad_value, (1, pad[3], 1))
    img_padded = np.concatenate((img_padded, pad_right), axis=1)

    return img_padded, pad
