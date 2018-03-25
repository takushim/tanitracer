#!/usr/bin/env python

import sys, argparse, pandas, tifffile, numpy
from taniguchi import spotmarker

# prepare spot marker
marker = spotmarker.SpotMarker()

# defaults
input_filename = 'test.tif'
marker_filename = 'test.txt'
output_filename = 'output.tif'
invert_image = False

# parse arguments
parser = argparse.ArgumentParser(description='plot centroids to check gaussian fitting.', \
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--output-file', nargs=1, default=[output_filename], \
                    help='output multipage-tiff file with markers')

parser.add_argument('-f', '--marker-file', nargs=1, default=[marker_filename], \
                    help='read marker tsv file and no running')
parser.add_argument('-z', '--marker-size', nargs=1, type=int, default=[marker.marker_size], \
                    help='marker size to plot')
parser.add_argument('-c', '--marker-colors', nargs=3, type=str, default=marker.marker_colors, \
                    metavar=('NEW', 'CONT', 'END'), \
                    help='marker colors for new/continued/end spots')

parser.add_argument('-i', '--invert-image', action='store_true', default=invert_image, \
                    help='invert image look-up table')

parser.add_argument('input_file', nargs='?', default=input_filename, \
                    help='input multpage-tiff file to plot markers')

args = parser.parse_args()

# set arguments
input_filename = args.input_file
output_filename = args.output_file[0]
marker_filename = args.marker_file[0]
marker.marker_size = args.marker_size[0]
marker.marker_colors = args.marker_colors
invert_image = args.invert_image

# read image
orig_image = tifffile.imread(input_filename)
if len(orig_image.shape) == 2:
    orig_image = numpy.array([orig_image])

# convert image to 8-bit RGB color
image_color = marker.convert_to_color(orig_image)
if invert_image is True:
    image_color = 255 - image_color

# read results
spot_table = pandas.read_table(marker_filename, comment = '#')

# mark tracking status
spot_status = marker.tracking_status(spot_table)
image_color = marker.mark_spots(image_color, spot_table, spot_status)

# output multipage tiff
tifffile.imsave(output_filename, image_color)

