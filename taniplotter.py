#!/usr/bin/env python

import os, platform, sys, glob, argparse
import pandas, tifffile, numpy
from taniguchi import spotplotter

# prepare spot marker
plotter = spotplotter.SpotPlotter()

# defaults
input_filenames = None
image_size = None
align_spots = True
align_filename = 'align.txt'
output_filename = 'output.tif'

# parse arguments
parser = argparse.ArgumentParser(description='make super-resolution image from spot centroids.', \
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-o', '--output-file', nargs=1, default=[output_filename], \
                    help='output super-resolution tiff file')

parser.add_argument('-n', '--no-align', action='store_true', default=(align_spots is False), \
                    help='plot without alignment')
parser.add_argument('-a', '--align-file', nargs=1, default=[align_filename], \
                    help='tsv file with alignment (align.txt if not specified)')
parser.add_argument('-e', '--align-each', nargs=1, type=int, default=[plotter.align_each], \
                    help='tsv file with alignment (align.txt if not specified)')
                    
parser.add_argument('-x', '--image-scale', nargs=1, type=int, default=[plotter.image_scale], \
                    help='scale factor to original image')
parser.add_argument('-z', '--image-size', nargs=2, type=int, default=image_size, \
                    metavar=('WIDTH', 'HEIGHT'), \
                    help='size of original image (read from first file if not specified)')

parser.add_argument('input_file', nargs='+', default=None, \
                    help='input tsv file(s) with plotting geometries')

args = parser.parse_args()

# collect input filenames
if (platform.system() == "Windows"):
    input_filenames = []
    for pattern in args.input_file:
        input_filenames.extend(sorted(glob.glob(pattern)))
else:
    input_filenames = args.input_file

# set arguments
align_spots = (args.no_align is False)
align_filename = args.align_file[0]
image_size = args.image_size
plotter.align_each = args.align_each[0]
plotter.image_scale = args.image_scale[0]

# read align table
if align_spots is True:
    align_table = pandas.read_table(align_filename, comment = '#')

# read first table and determine size
if image_size is None:
    width, height = plotter.find_image_size(input_filenames[0])
else:            
    width, height = image_size[0], image_size[1]

print(width, height)
sys.exit()

# plot spot table(s)
output_image = numpy.zeros((height, width), dtype=numpy.int32)

#for input_filename in input_filenames:

