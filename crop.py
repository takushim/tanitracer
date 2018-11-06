#!/usr/bin/python

import os, sys, argparse, numpy
from skimage.external import tifffile

scale = 8
width = scale * 450
height = scale * 450
x = scale * 0
y = scale * 62

parser = argparse.ArgumentParser(description='Image Cropper for 32-bit TIFF', \
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--output-image', nargs=1, default = [output_image_filename], \
                    help='output image file name ([basename]_crop.tif if not specified)')

parser.add_argument('-t', '--output-tsv', nargs=1, default = [output_tsv_filename], \
                    help='output tsv file name(heatmap.txt if not specified)')

parser.add_argument('input_file', nargs=1, default=None, \
                    help='input tiff file')
args = parser.parse_args()


input_files = sys.argv[1:]

for input_file in input_files:
    output_file = os.path.splitext(os.path.basename(input_file))[0] + '_crop.tif'
    if input_file == output_file:
        raise Exception('input_filename == output_filename')

    image = tifffile.imread(input_file)
    print("Input:", image.shape, image.dtype)
    output = image[y:(y+height), x:(x+width)]
    print("Output:",output.shape, output.dtype)

    tifffile.imsave(output_file, output)
