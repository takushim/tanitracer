#!/usr/bin/env python

import os, platform, sys, argparse, numpy, math
from PIL import Image, ImageDraw, ImageFont
from skimage.external import tifffile

# defaults
input_filename = None
output_filename = None
scale = 4
extend = 30
maxpage = 50
bar_length = 10 # in px at scale = 1.0
bar_width = 8 # in px at the final scale
interval = 1.0
crop = [0, 0, -1, -1]
title = ""

# font settings
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
parser = argparse.ArgumentParser(description='put scale and stamp to multipage tiff', \
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--output-file', nargs=1, default=output_filename, \
                    help='output multipage-tiff file ([basename]_mov.tif if not specified)')
parser.add_argument('-c', '--crop', nargs=4, type=int, default=crop, \
                    metavar = ('X', 'Y', 'WIDTH', 'HEIGHT'), \
                    help='cropping of the original image. minus values in w/h use the max w/h')
parser.add_argument('-t', '--title', nargs=1, default=[title], \
                    help='title (or caption)')
parser.add_argument('-x', '--scale', nargs=1, type=int, default=[scale], \
                    help='magnification sacle')
parser.add_argument('-e', '--extend', nargs=1, type=int, default=[extend], \
                    help='extension at the bottom (px)')
parser.add_argument('-m', '--maxpage', nargs=1, type=int, default=[maxpage], \
                    help='max page size')
parser.add_argument('-l', '--bar-length', nargs=1, type=int, default=[bar_length], \
                    help='length of bar (px) at scale = 1.0')
parser.add_argument('-w', '--bar-width', nargs=1, type=int, default=[bar_width], \
                    help='width of bar (px) at final scale')
parser.add_argument('-i', '--interval', nargs=1, type=float, default=[interval], \
                    help='interval of time stamp')
parser.add_argument('input_file', nargs=1, default=input_filename, \
                    help='input file (multipage-tiff file) to trace spots')

args = parser.parse_args()

# set arguments
input_filename = args.input_file[0]
title = args.title[0]
scale = args.scale[0]
extend = args.extend[0]
maxpage = args.maxpage[0]
interval = args.interval[0]
bar_length = args.bar_length[0]
bar_width = args.bar_width[0]
crop = args.crop

if args.output_file is None:
    output_filename = os.path.splitext(os.path.basename(input_filename))[0] + '_mov.tif'
    if input_filename == output_filename:
        raise Exception('input_filename == output_filename')
else:
    output_filename = args.output_file[0]

# read image
orig_images = tifffile.imread(input_filename)
x, y, width, height = crop
if crop[2] < 0:
    width = orig_images.shape[2] - x
if crop[3] < 0:
    height = orig_images.shape[1] - x
pages = min(maxpage, orig_images.shape[0])
orig_images = orig_images[0:pages, y:(y + height), x:(x + width)]

# output image
if len(orig_images.shape) == 3:
    output_images = numpy.full((pages, height * scale + extend, width * scale), 255, dtype = numpy.uint8)
else:
    output_images = numpy.full((pages, height * scale + extend, width * scale, 3), 255, dtype = numpy.uint8)

# magnify images
for page in range(pages):
    image = Image.fromarray(orig_images[page])
    image = image.resize((width * scale, height * scale))
    output_images[page, 0:(height * scale)] = numpy.asarray(image)

# put scale and stamp
font = ImageFont.truetype(font_file, font_size)
digits = math.floor(math.log10(interval))
if digits >= 0:
    stamp_format = "%d s (%s)"
else:
    stamp_format = "%%.%df s (%%s)" % (abs(digits))

# calculate text size
image = Image.fromarray(orig_images[0])
draw = ImageDraw.Draw(image)
text_height = 0
text_width = 0
for page in range(pages):
    text = stamp_format % (page * interval, title)
    this_width, this_height = draw.textsize(text, font = font)
    text_height = max(text_height, this_height)
    text_width = max(text_height, this_width)

# draw time _stamp
for page in range(pages):
    # get drawer
    image = Image.fromarray(output_images[page])
    draw = ImageDraw.Draw(image)

    # time stamp
    text = stamp_format % (page * interval, title)
    this_width, this_height = draw.textsize(text, font = font)
    font_padding = int((extend - text_height) / 2)
    x = width * scale - font_padding - this_width - int(extend / 4)
    #x = int(extend / 2) + text_width - this_width
    y = height * scale + extend - font_padding - this_height
    draw.text((x, y), text, font = font, fill = font_color)

    # scale
    x = int(extend / 2)
    #x = (width - bar_length) * scale - int(extend / 2)
    y = height * scale + int(extend / 2)
    draw.line((x, y, x + bar_length * scale, y), fill = font_color, width = bar_width)

    # put it back
    output_images[page] = numpy.asarray(image)

tifffile.imsave(output_filename, output_images)