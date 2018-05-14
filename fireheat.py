#!/usr/bin/env python

import sys, argparse, numpy
from matplotlib import pylab
from taniclass import firefrc
from skimage.external import tifffile

# prepare resolver
resolver = firefrc.FireFRC()

# defaults
input_filename1 = None
input_filename2 = None
output_image_filename = 'heatmap.tif'
output_tsv_filename = 'heatmap.txt'
output_histgram_filename = 'histgram.tif'
output_histgram = False
mask_image_filename = None

parser = argparse.ArgumentParser(description='Make FIRE/FRC heatmap using 2 split images', \
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--output-image', nargs=1, default = [output_image_filename], \
                    help='output image file name(heatmap.tif if not specified)')

parser.add_argument('-t', '--output-tsv', nargs=1, default = [output_tsv_filename], \
                    help='output tsv file name(heatmap.txt if not specified)')

parser.add_argument('-G', '--output-histgram', action='store_true', default=output_histgram, \
                    help='output histgram image tiff')
parser.add_argument('-g', '--output-histgram-file', nargs=1, default = [output_histgram_filename], \
                    help='output histgram image file name (histgram.tif if not specified)')

parser.add_argument('-m', '--mask-image', nargs=1, default = [mask_image_filename], \
                    help='mask image file name')

parser.add_argument('input_file', nargs=2, default=None, \
                    help='input SQUARE tiff files (image1, image2)')
args = parser.parse_args()

input_filename1 = args.input_file[0]
input_filename2 = args.input_file[1]
output_image_filename = args.output_image[0]
output_tsv_filename = args.output_tsv[0]

output_histgram = args.output_histgram
output_histgram_filename = args.output_histgram_file[0]

mask_image_filename = args.mask_image[0]

image1 = tifffile.imread(input_filename1)
image2 = tifffile.imread(input_filename2)

if image1.shape != image2.shape:
    raise Exception('images must be identical size')
    
if (image1.shape[0] % 128 != 0) or (image1.shape[1] % 128 != 0):
    raise Exception('images width/height must be multiple of 128 px')

size_x = image1.shape[1] // 64 - 1
size_y = image2.shape[0] // 64 - 1
    
# prepare masking
# masking array for fire_array
mask_array = numpy.ones((size_y, size_x), dtype=numpy.int)
if mask_image_filename is not None:
    # read masking image
    mask_image = tifffile.imread(mask_image_filename)
    mask_image = mask_image.astype(numpy.bool).astype(numpy.uint8)        
    # mask image
    image1 = image1 * mask_image
    image2 = image2 * mask_image
    for index_y in range(size_y):
        for index_x in range(size_x):
            # origin to copy image
            x0 = 64 * index_x
            y0 = 64 * index_y
            #mask_array[index_y, index_x] = numpy.prod(mask_image[y0:(y0 + 128), x0:(x0 + 128)])
            total = mask_image[y0:(y0 + 128), x0:(x0 + 128)].size
            masked = numpy.sum(mask_image[y0:(y0 + 128), x0:(x0 + 128)] == 0)
            if 1.0 * masked / total > 0.1:
                mask_array[index_y, index_x] = 0

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
        
        # calculate fire only for unmasked area (to prevent zero error)
        if mask_array[index_y, index_x] == 0:
            fire_array[index_y, index_x] = numpy.nan
        else:
            sf, fsc = resolver.fourier_spin_correlation(image1_128px, image2_128px)
            smooth_fsc = resolver.smoothing_fsc(sf, fsc)
            sf_fix17 = resolver.intersection_threshold(sf, smooth_fsc)
            
            if len(sf_fix17) > 0:
                fire_array[index_y, index_x] = 2.0 / sf_fix17[0]
            else:
                print("fire not determined at index = (%d, %d)" % (index_x, index_y))
                print(smooth_fsc)
                fire_array[index_y, index_x] = numpy.nan

print("mean fire: %f (min: %f, max %f)" % (numpy.nanmean(fire_array), numpy.nanmin(fire_array), numpy.nanmax(fire_array)))

# output tsv
numpy.savetxt(output_tsv_filename, fire_array, delimiter='\t')

# output heatmap
output_image = numpy.zeros(image1.shape, numpy.uint8)

fire_array_heatmap = fire_array.clip(1, 10)
max_value = numpy.nanmax(fire_array_heatmap)
min_value = numpy.nanmin(fire_array_heatmap)
fire_array_heatmap[numpy.isnan(fire_array_heatmap)] = max_value

for index_y in range(size_y):
    for index_x in range(size_x):
        x0 = 64 * index_x + 32
        y0 = 64 * index_y + 32
        ratio = (fire_array_heatmap[index_y, index_x] - min_value) / (max_value - min_value)
        output_image[y0:(y0 + 64), x0:(x0 + 64)] = int(255 * (1 - ratio))

# corners
ratio = (fire_array_heatmap[0, 0] - min_value) / (max_value - min_value)
output_image[0:32, 0:32] = int(255 * (1 - ratio))
ratio = (fire_array_heatmap[0, -1] - min_value) / (max_value - min_value)
output_image[0:32, -32:] = int(255 * (1 - ratio))
ratio = (fire_array_heatmap[-1, 0] - min_value) / (max_value - min_value)
output_image[-32:, 0:32] = int(255 * (1 - ratio))
ratio = (fire_array_heatmap[-1, -1] - min_value) / (max_value - min_value)
output_image[-32:, -32:] = int(255 * (1 - ratio))

# upper/bottom sides
for index_x in range(size_x):
    x0 = 64 * index_x + 32
    ratio = (fire_array_heatmap[0, index_x] - min_value) / (max_value - min_value)
    output_image[0:32, x0:(x0 + 64)] = int(255 * (1 - ratio))
    ratio = (fire_array_heatmap[-1, index_x] - min_value) / (max_value - min_value)
    output_image[-32:, x0:(x0 + 64)] = int(255 * (1 - ratio))

# left/right sides
for index_y in range(size_y):
    y0 = 64 * index_y + 32
    ratio = (fire_array_heatmap[index_y, 0] - min_value) / (max_value - min_value)
    output_image[y0:(y0 + 64), 0:32] = int(255 * (1 - ratio))
    ratio = (fire_array_heatmap[index_y, -1] - min_value) / (max_value - min_value)
    output_image[y0:(y0 + 64), -32:] = int(255 * (1 - ratio))

# output heatmap tiff
print("Output image file to %s." % (output_image_filename))
tifffile.imsave(output_image_filename, output_image)

# output histgram
if output_histgram is True:
    pylab.hist(fire_array[~numpy.isnan(fire_array)], bins=50)
    pylab.xlabel("fire (pixel)")
    pylab.ylabel("counts")
    pylab.savefig(output_histgram_filename, dpi=100, pad_inches=0.0, bbox_inches='tight')
    print("Output histgram image to %s." % (output_histgram_filename))

