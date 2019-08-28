#!/usr/bin/env python

import os, platform, sys, argparse, numpy, math
from PIL import Image, ImageDraw, ImageFont
from skimage.external import tifffile

# defaults
input_filename = None
output_filename = None
interval = 1.0
font_padding = 5
font_size = 24
font_color = 'black'
if platform.system() == "Windows":
    font_file = 'C:/Windows/Fonts/Arial.ttf'
elif platform.system() == "Linux":
    font_file = '/usr/share/fonts/dejavu/DejaVuSans.ttf'
elif platform.system() == "Darwin":
    font_file = '/Library/Fonts/Verdana.ttf'
else:
    raise Exception('font file error.')

# parse arguments
parser = argparse.ArgumentParser(description='draw time stamp into multipage tiff', \
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--output-file', nargs=1, default=output_filename, \
                    help='output multipage-tiff file ([basename]_stamp.tif if not specified)')

parser.add_argument('-i', '--interval', nargs=1, type=float, default=[interval], \
                    help='interval of time stamp')

parser.add_argument('-p', '--font-padding', nargs=1, type=int, default=[font_padding], \
                    help='padding from the corner (px)')

parser.add_argument('-z', '--font-size', nargs=1, type=int, default=[font_size], \
                    help='font size')

parser.add_argument('input_file', nargs=1, default=input_filename, \
                    help='input file (multipage-tiff file) to trace spots')

args = parser.parse_args()

# set arguments
input_filename = args.input_file[0]
interval = args.interval[0]
font_padding = args.font_padding[0]
font_size = args.font_size[0]

if args.output_file is None:
    output_filename = os.path.splitext(os.path.basename(input_filename))[0] + '_stamp.tif'
    if input_filename == output_filename:
        raise Exception('input_filename == output_filename')
else:
    output_filename = args.output_file[0]

# read image
orig_images = tifffile.imread(input_filename)
image_width = orig_images.shape[2]
image_height = orig_images.shape[1]
print(orig_images.shape)

# prepare font
font = ImageFont.truetype(font_file, font_size)

# output image
output_images = numpy.zeros(orig_images.shape, dtype = numpy.uint8)
print(output_images.shape)

# set format
digits = math.floor(math.log10(interval))
if digits >= 0:
    stamp_format = "%d s"
else:
    stamp_format = "%%.%df s" % (abs(digits))

# draw time _stamp
for index in range(len(orig_images)):
    image = Image.fromarray(orig_images[index])
    draw = ImageDraw.Draw(image)

    text = stamp_format % (index * interval)
    #print(index, text)

    text_width, text_height = draw.textsize(text, font = font)
    x = image_width - font_padding - text_width
    y = image_height - font_padding - text_height
    draw.text((x, y), text, font = font, fill = font_color)
    output_images[index] = numpy.asarray(image)

# output image
tifffile.imsave(output_filename, output_images)
