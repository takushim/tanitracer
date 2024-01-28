#!/usr/bin/env python

import os, sys, argparse, numpy, tifffile
from taniclass import gaussian8

# classes
tracer = gaussian8.Gaussian8()

# default values
input_filename = None
output_filename = None

# parse arguments
parser = argparse.ArgumentParser(description='Check the effect of LoG filter', \
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--output-file', nargs=1, default=output_filename, \
                    help='output multipage TIFF file ([basename]_log.tif if not specified)')

parser.add_argument('-l', '--laplace', nargs=1, type=float, default=tracer.laplace, \
                    help='sigma of LoG filter (try near the pixel diameter of spots)')

parser.add_argument('input_file', nargs=1, default=input_filename, \
                    help='input (multipage) TIFF file to apply filter')

args = parser.parse_args()

# set arguments
tracer.laplace = args.laplace[0]
input_filename = args.input_file[0]

if args.output_file is None:
    #output_filename = os.path.splitext(os.path.basename(input_filename))[0] + ("_l%.2f.tif" % tracer.laplace)
    output_filename = os.path.splitext(os.path.basename(input_filename))[0] + '_log.tif'
    if input_filename == output_filename:
        raise Exception('input_filename == output_filename')
else:
    output_filename = args.output_file[0]

# read image
orig_images = tifffile.imread(input_filename)
if len(orig_images.shape) == 2:
    orig_images = numpy.array([orig_images])

# apply log filter
float_images = numpy.array(orig_images, 'f')
tracer.set_image_clip(orig_images)
float_images = tracer.clip_array(float_images)
for index in range(len(float_images)):
    float_images[index] = tracer.standardize_and_filter_image(float_images[index])

# prepare image of 8-bit RGB color
float_max = numpy.max(float_images)
float_min = numpy.min(float_images)
output_images = (65535.0 * (float_images - float_min) / (float_max - float_min)).astype(numpy.uint16)

# output image
tifffile.imwrite(output_filename, output_images)
