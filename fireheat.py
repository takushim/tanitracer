#!/usr/bin/env python

import sys, argparse, numpy
import matplotlib.pyplot as pyplot
from taniclass import firefrc
from skimage.external import tifffile

# prepare resolver
resolver = firefrc.FireFRC()

# defaults
input_filename1 = None
input_filename2 = None
output_image_filename = 'heatmap.tif'

parser = argparse.ArgumentParser(description='Make FIRE/FRC heatmap using 2 split images', \
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--output-image', nargs=1, default = [output_image_filename], \
                    help='output image file name(heatmap.tif if not specified)')
parser.add_argument('input_file', nargs=2, default=None, \
                    help='input SQUARE tiff files (image1, image2)')
args = parser.parse_args()

input_filename1 = args.input_file[0]
input_filename2 = args.input_file[1]
output_image_filename = args.output_image[0]

image1 = tifffile.imread(input_filename1)
image2 = tifffile.imread(input_filename2)

if image1.shape != image2.shape:
    raise Exception('images must be identical size')
    
if (image1.shape[0] % 128 != 0) or (image1.shape[1] % 128 != 0):
    raise Exception('images width/height must be multiple of 128 px')

size_x = image1.shape[1] // 64 - 1
size_y = image2.shape[0] // 64 - 1

fire_array = numpy.zeros((size_y, size_x), dtype=numpy.float)
image1_128px = numpy.zeros((128, 128), dtype=numpy.int)
image2_128px = numpy.zeros((128, 128), dtype=numpy.int)

for index_y in range(size_y):
    for index_x in range(size_x):
        # origin to copy image
        x0 = 64 * index_x
        y0 = 64 * index_y
        
        image1_128px = image1[y0:(y0 + 128), x0:(x0 + 128)]
        image2_128px = image2[y0:(y0 + 128), x0:(x0 + 128)]
        
        sf, fsc = resolver.fourier_spin_correlation(image1_128px, image2_128px)
        smooth_fsc = resolver.smoothing_fsc(sf, fsc)
        sf_fix17 = resolver.intersection_threshold(sf, smooth_fsc)
        
        fire_array[index_y, index_x] = 2.0 / sf_fix17[0]

print("mean fire: %f (min: %f, max %f)" % (numpy.mean(fire_array), numpy.min(fire_array), numpy.max(fire_array)))

output_image = numpy.zeros(image1.shape, numpy.uint8)

fire_array = fire_array.clip(1, 10)
max_value = numpy.max(fire_array)
min_value = numpy.min(fire_array)

for index_y in range(size_y):
    for index_x in range(size_x):
        x0 = 64 * index_x + 32
        y0 = 64 * index_y + 32
        ratio = (fire_array[index_y, index_x] - min_value) / (max_value - min_value)
        output_image[y0:(y0 + 64), x0:(x0 + 64)] = int(255 * (1 - ratio))

# output heatmap tiff
print("Output image file to %s." % (output_image_filename))
tifffile.imsave(output_image_filename, output_image)

