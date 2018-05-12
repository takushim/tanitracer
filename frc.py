#!/usr/bin/env python

import os, platform, sys, glob, argparse
import numpy, pandas
import matplotlib.pyplot as pyplot
from taniext import fourier_ring_corr
from taniclass import firefrc
from PIL import Image
from skimage.external import tifffile

# prepare resolver
resolver = firefrc.FireFRC()

# defaults
input_filename1 = None
input_filename2 = None

parser = argparse.ArgumentParser(description='Calculate FRC between 2 images', \
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('input_file', nargs=2, default=None, \
                    help='input multpage-tiff files (image1, image2)')
args = parser.parse_args()

input_filename1 = args.input_file[0]
input_filename2 = args.input_file[1]

image1 = tifffile.imread(input_filename1)
image2 = tifffile.imread(input_filename2)

x1, FSC, x2, T, SNRt = fourier_ring_corr.FSC(image1, image2)

smooth_FSC = resolver.smoothing_fsc(x1, FSC)
sf_fix17 = resolver.intersection_threshold(x1, smooth_FSC)
print("resolution candidates: ", sf_fix17)

pyplot.plot(x1,FSC,label = 'FSC')
pyplot.plot(x1, smooth_FSC, label = 'sm_fsc')
#pyplot.plot(x2,T,'--',label = 'Threshold SNR = '+str(SNRt))
pyplot.xlim(0,1)
pyplot.legend()
pyplot.xlabel('Spatial Frequency/Nyquist')
pyplot.show()

#pyplot.savefig('output.tif')

