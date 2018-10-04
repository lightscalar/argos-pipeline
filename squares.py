import numpy as np
import cv2
import os
import imutils
from ipdb import set_trace as debug


def create_rotated_pics(img, row, col, size, num_rotations):
    """Extract rotated tiles from an image."""

    images = []

    rows, cols, chans = img.shape

    shift_right = col < size / 2
    shift_left = col > cols - size / 2
    shift_down = row < size / 2
    shift_up = row > rows - size / 2

    #    os.makedirs('New_images')
    if shift_right + shift_left + shift_down + shift_up > 0:
        if shift_right:
            col = size / 2
        if shift_left:
            col = cols - size / 2
        if shift_down:
            row = size / 2
        if shift_up:
            row = rows - size / 2
        col_low = int(col - size / 2)
        col_high = int(col + size / 2)
        row_low = int(row - size / 2)
        row_high = int(row + size / 2)
        square = img[row_low:row_high, col_low:col_high, :]
        images.append(square)

    elif (
        col < size * np.sqrt(2) / 2
        or col > cols - size * np.sqrt(2) / 2
        or row < size * np.sqrt(2) / 2
        or row > rows - size * np.sqrt(2) / 2
    ):
        col_low = int(col - size / 2)
        col_high = int(col + size / 2)
        row_low = int(row - size / 2)
        row_high = int(row + size / 2)
        square = img[row_low:row_high, col_low:col_high, :]
        images.append(square)
    #        cv2.imwrite('New_images/image.jpg',square)

    else:
        col_low = int(col - np.sqrt(2) * size / 2)
        col_high = int(col + np.sqrt(2) * size / 2)
        row_low = int(row - np.sqrt(2) * size / 2)
        row_high = int(row + np.sqrt(2) * size / 2)
        angle_per_iteration = int(360 / num_rotations)
        img_ = img[row_low:row_high, col_low:col_high, :]
        ctr = int(np.sqrt(2) * size / 2)
        ctr_plus = int(ctr + size / 2)
        ctr_minus = int(ctr - size / 2)

        for itr in range(num_rotations):
            rotation_angle = angle_per_iteration * itr
            if rotation_angle > 0:
                rotated_image = imutils.rotate(img_, rotation_angle)
            else:
                rotated_image = img_
            square = rotated_image[ctr_minus:ctr_plus, ctr_minus:ctr_plus, :]
            images.append(square)

    return images


if __name__ == "__main__":
    create_rotated_pics(1200, 0, 200, 4)
