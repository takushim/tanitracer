#!/usr/bin/env python

import sys, argparse, numpy
from skimage.external import tifffile

# defaults
input_filename = None
output_image_filename1 = 'split_image1.tif'
output_image_filename2 = 'split_image2.tif'

parser = argparse.ArgumentParser(description='Split image randomly for FRC/FIRE', \
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('input_file', nargs=1, default=None, \
                    help='input tiff file to split')
args = parser.parse_args()

input_filename = args.input_file[0]

input_image = tifffile.imread(input_filename)
input_image = input_image.astype(numpy.int)
if len(input_image.shape) != 2:
    raise Exception('images must be grayscale single-page')

height, width = input_image.shape[0], input_image.shape[1]

output_image1 = numpy.zeros(input_image.shape, numpy.int)
output_image2 = numpy.zeros(input_image.shape, numpy.int)

for y in range(height):
    for x in range(width):
        output_image1[y,x] = numpy.sum(numpy.random.randint(2, size=input_image[y,x]))
        output_image2[y,x] = input_image[y,x] - output_image1[y,x]

tifffile.imsave(output_image_filename1, output_image1)
tifffile.imsave(output_image_filename2, output_image2)
