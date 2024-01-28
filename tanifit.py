#!/usr/bin/env python

import os, platform, sys, argparse, numpy, itertools, tifffile
from taniclass import gaussian8, spotmarker
from PIL import Image, ImageDraw, ImageFont

# prepare tracing library
tracer = gaussian8.Gaussian8()
marker = spotmarker.SpotMarker()

# defaults
input_filename = None
output_filename = None
use_plane = 0
laplaces = [tracer.laplace]
min_distances = [tracer.min_distance]
threshold_abses = [tracer.threshold_abs]

if platform.system() == "Windows":
    font_file = 'C:/Windows/Fonts/Arial.ttf'
elif platform.system() == "Linux":
    font_file = '/usr/share/fonts/dejavu/DejaVuSans.ttf'
elif platform.system() == "Darwin":
    font_file = '/Library/Fonts/Verdana.ttf'
else:
    raise Exception('font file error.')
font_size = 20
font_color = 'white'

# parse arguments
parser = argparse.ArgumentParser(description='Try detecting fluorescent spots changing parameters', \
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--output-file', nargs=1, default=output_filename, \
                    help='output multipage TIFF file ([basename]_fit.tif if not specified)')

parser.add_argument('-p', '--use-plane', nargs=1, type=int, default=[use_plane], \
                    help='frame to detect spots (the first frame if not specified)')

parser.add_argument('-x', '--max-diameter', nargs=1, type=float, default=[tracer.max_diameter], \
                    help='limit the maximum diameter of spots (to avoid abnormal fitting)')

parser.add_argument('-z', '--marker-size', nargs=1, type=int, default=[marker.marker_size], \
                    help='marker size to draw detected spots')
parser.add_argument('-c', '--marker-colors', nargs=2, type=str, \
                    metavar = ('NORMAL', 'REDUNDANT'), \
                    default=[marker.marker_colors[0], marker.marker_colors[3]],
                    help='marker colors to draw spots detected normally and redundantly')

parser.add_argument('-i', '--invert-image', action='store_true', default=marker.invert_image, \
                    help='invert the LUT of output image')

group = parser.add_mutually_exclusive_group()
group.add_argument('-m', '--min-distance', nargs=1, type=int, default=min_distances, \
                    help='pixel area to find local max (usually use default)')
group.add_argument('-M', '--min-distance-range', nargs=3, type=int,\
                    metavar=('BEGIN', 'END', 'STEP'), \
                    help='range of "min distance" to try (specify by integers)')

group = parser.add_mutually_exclusive_group()
group.add_argument('-l', '--laplace', nargs=1, type=float, default=laplaces, \
                    help='sigma of LoG filter (try near the pixel diameter of spots)')
group.add_argument('-L', '--laplace-range', nargs=3, type=float,\
                    metavar=('BEGIN', 'END', 'STEP'), \
                    help='range of "laplace" to try (specify by floats)')

group = parser.add_mutually_exclusive_group()
group.add_argument('-t', '--threshold-abs', nargs=1, type=float, default=threshold_abses, \
                    help='threshold of Gaussian fitting')
group.add_argument('-T', '--threshold-abs-range', nargs=3, type=float, \
                    metavar=('BEGIN', 'END', 'STEP'), \
                    help='range of "threshod abs" to tru (specify by floats)')

parser.add_argument('input_file', nargs=1, default=input_filename, \
                    help='input (multipage) TIFF file')

args = parser.parse_args()

# set arguments
input_filename = args.input_file[0]
use_plane = args.use_plane[0]
marker.marker_colors = [args.marker_colors[0] for i in range(3)] + [args.marker_colors[1]]
marker.marker_size = args.marker_size[0]
marker.invert_image = args.invert_image
tracer.max_diameter = args.max_diameter[0]

if args.output_file is None:
    output_filename = os.path.splitext(os.path.basename(input_filename))[0] + '_fit.tif'
    if input_filename == output_filename:
        raise Exception('input_filename == output_filename')
else:
    output_filename = args.output_file[0]

# set ranged arguments
min_distances = args.min_distance
if args.min_distance_range is not None:
    min_distances = numpy.arange(*args.min_distance_range)
laplaces = args.laplace
if args.laplace_range is not None:
    laplaces = numpy.arange(*args.laplace_range)
threshold_abses = args.threshold_abs
if args.threshold_abs_range is not None:
    threshold_abses = numpy.arange(*args.threshold_abs_range)

# read image (one plane only)
orig_image = tifffile.imread(input_filename)
if len(orig_image.shape) > 2:
    orig_image = orig_image[use_plane]

# image clip
tracer.set_image_clip(orig_image)

# prepare image of 8-bit RGB color (one plane only)
image_color = marker.convert_to_color(numpy.array([orig_image]))[0]

# prepare font
font = ImageFont.truetype(font_file, font_size)

# conditions
conditions = list(itertools.product(min_distances, laplaces, threshold_abses))

# output images
output_images = numpy.zeros((len(conditions), orig_image.shape[0], orig_image.shape[1], 3), dtype = numpy.uint8)
font_images = numpy.zeros((len(conditions), font_size, orig_image.shape[1], 3), dtype = numpy.uint8)
count_images = numpy.zeros((len(conditions), font_size, orig_image.shape[1], 3), dtype = numpy.uint8)

for index, condition in enumerate(conditions):
    # parse parameters
    (min_distance, laplace, threshold_abs) = condition

    # set tracer, and get results
    tracer.laplace = laplace
    tracer.min_distance = min_distance
    tracer.threshold_abs = threshold_abs
    results = tracer.fitting_image_array(orig_image)

    # draw results
    image_draw = image_color.copy()
    if len(results) > 0:
        image_draw = marker.mark_spots(numpy.array([image_draw]), results)[0]
    output_images[index] = image_draw

    # draw condition
    image = Image.fromarray(font_images[index])
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), "L %.2f T %.5f M %d" % (laplace, threshold_abs, min_distance), font = font, fill = font_color)
    font_images[index] = numpy.asarray(image)

    # count spots
    image = Image.fromarray(count_images[index])
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), "C: %d" % (len(results)), font = font, fill = font_color)
    count_images[index] = numpy.asarray(image)

    # radius (= laplacian)
    radii = numpy.array(results['diameter'].dropna().tolist()) / 2.0
    rel95 = 2.262 * numpy.sqrt(numpy.var(radii, ddof=1) / len(radii))

    print("Plot %d spots with: M = %d, L = %f, T = %f. Radius = %f +/- %f." % \
            (len(results), min_distance, laplace, threshold_abs, numpy.average(radii), rel95))
    print(".")

# combine images and output
output_images = numpy.hstack((output_images, font_images, count_images))
tifffile.imwrite(output_filename, output_images)
