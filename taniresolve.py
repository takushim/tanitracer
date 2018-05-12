#!/usr/bin/env python

import os, platform, sys, argparse
import numpy
import matplotlib.pyplot as pyplot
from taniclass import firefrc
from skimage.external import tifffile

# prepare resolver
resolver = firefrc.FireFRC()

# defaults
input_filename1 = None
input_filename2 = None

parser = argparse.ArgumentParser(description='Calculate FRC between 2 images', \
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('input_file', nargs=2, default=None, \
                    help='input SQUARE multpage-tiff files (image1, image2)')
args = parser.parse_args()

input_filename1 = args.input_file[0]
input_filename2 = args.input_file[1]

image1 = tifffile.imread(input_filename1)
image2 = tifffile.imread(input_filename2)

sf, fsc = resolver.fourier_spin_correlation(image1, image2)

smooth_fsc = resolver.smoothing_fsc(sf, fsc)

sf_fix17 = resolver.intersection_threshold(sf, smooth_fsc)
print("resolution candidates: ", sf_fix17)

pyplot.plot(sf, fsc, label = 'fsc')
pyplot.plot(sf, smooth_fsc, label = 'sm_fsc')
pyplot.xlim(0, 1.0)
pyplot.ylim(0, 1.2)
pyplot.vlines(sf_fix17, 0, 1.2)
pyplot.hlines(0.1427, 0, 1)
pyplot.xlabel('Spatial Frequency')
pyplot.show()

#pyplot.savefig('output.tif')
