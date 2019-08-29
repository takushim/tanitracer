#!/usr/bin/env python

import os, platform, sys, argparse, numpy
import cv2
from skimage.external import tifffile

# defaults
extension = ".mp4" # do not forget "." before extension
fourcc = "mp4v"
input_filename = None
output_filename = None
fps = 10.0

# parse arguments
parser = argparse.ArgumentParser(description='make movie from multipage tiff', \
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--output-file', nargs=1, default=output_filename, \
                    help='output movie file ([basename].[mp4/avi] if not specified)')
parser.add_argument('-f', '--fps', nargs=1, type=float, default=[fps], \
                    help='frame per second')
parser.add_argument('input_file', nargs=1, default=input_filename, \
                    help='input file (multipage-tiff file)')
args = parser.parse_args()

# parameters
input_filename = args.input_file[0]
fps = args.fps[0]
if args.output_file is None:
    output_filename = os.path.splitext(os.path.basename(input_filename))[0] + extension
    if input_filename == output_filename:
        raise Exception('input_filename == output_filename')
else:
    output_filename = os.path.splitext(args.output_file[0])[0] + extension

# read tiff
orig_images = tifffile.imread(input_filename)
size = (orig_images.shape[2], orig_images.shape[1])

# output avi
fmt = cv2.VideoWriter_fourcc(*fourcc)
writer = cv2.VideoWriter(output_filename, fmt, fps, size)

for index in range(len(orig_images)):
    frame = cv2.cvtColor(orig_images[index], cv2.COLOR_RGB2BGR)
    writer.write(frame)

writer.release()

