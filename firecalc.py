#!/usr/bin/env python

import os, platform, sys, argparse, numpy, tifffile
import matplotlib.pyplot as pyplot
from taniclass import firefrc

# prepare resolver
resolver = firefrc.FireFRC()

# defaults
input_filename1 = None
input_filename2 = None
mask_image_filename = None
output_graph_filename = 'firefrc.tif'

parser = argparse.ArgumentParser(description='Calculate FIRE value from two super-resolved images', \
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-o', '--output-graph', nargs=1, default = [output_graph_filename], \
                    help='output graph file name (firefrc.tif if not specified)')

parser.add_argument('-m', '--mask-image', nargs=1, default = [mask_image_filename], \
                    help='read masking image to omit unnecessary area')

parser.add_argument('input_file', nargs=2, default=None, \
                    help='input TWO SQUARE single-page TIFF files (image1, image2)')
args = parser.parse_args()

input_filename1 = args.input_file[0]
input_filename2 = args.input_file[1]
mask_image_filename = args.mask_image[0]
output_graph_filename = args.output_graph[0]

image1 = tifffile.imread(input_filename1)
image2 = tifffile.imread(input_filename2)

# prepare masking
# masking array for fire_array
if mask_image_filename is not None:
    # read masking image
    mask_image = tifffile.imread(mask_image_filename)
    mask_image = mask_image.astype(bool).astype(numpy.uint8)
    # mask image
    image1 = image1 * mask_image
    image2 = image2 * mask_image

sf, fsc = resolver.fourier_spin_correlation(image1, image2)

smooth_fsc = resolver.smoothing_fsc(sf, fsc)

sf_fix17 = resolver.intersection_threshold(sf, smooth_fsc)
resolutions = 2.0 / sf_fix17
print("resolution (px): ", resolutions)

pyplot.plot(sf, fsc, label = 'fsc')
pyplot.plot(sf, smooth_fsc, label = 'sm_fsc')
pyplot.xlim(0, 1.0)
pyplot.ylim(0, 1.2)
pyplot.vlines(sf_fix17, 0, 1.2)
pyplot.hlines(0.1427, 0, 1)
pyplot.xlabel('Spatial Frequency')

pyplot.savefig(output_graph_filename)
pyplot.show()
