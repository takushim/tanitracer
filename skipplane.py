#!/usr/bin/python

import os, sys, argparse, numpy
from skimage.external import tifffile

skip_every = 10

parser = argparse.ArgumentParser(description='Image Cropper for 32-bit TIFF', \
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
#parser.add_argument('-o', '--output-image', nargs=1, default = [output_file], \
#                    help='output image file name ([basename]_skip.tif if not specified)')

parser.add_argument('-s', '--skip-every', nargs=1, type=int, default = [skip_every], \
                    help='skip every X plane')

parser.add_argument('input_file', nargs=1, default=None, \
                    help='input tiff file')
args = parser.parse_args()

skip_every = args.skip_every[0]
input_file = args.input_file[0]
output_file = os.path.splitext(os.path.basename(input_file))[0] + '_skip.tif'
if input_file == output_file:
    raise Exception('input_filename == output_filename')

image = tifffile.imread(input_file)
output = image[::skip_every]

tifffile.imsave(output_file, output)
