#!/usr/bin/env python

import sys, argparse
import pandas, cv2, tifffile
from taniguchi import siftdrift

input_filename = 'bf.tif'
output_filename = 'drift.txt'
output_image_filename = 'bf_corrected.tif'

parser = argparse.ArgumentParser(description='Calculate drift using SIFT algorithm', \
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--output-file', nargs=1, default=[output_file], \
                    help='tsv file to output')
parser.add_argument('-o', '--output-file', nargs=1, default=[output_file], \
                    help='tsv file to output')
parser.add_argument('input_file', nargs='?', default=[input_filename], \
                    help='input file (single 8bit multipage tiff of bright fields)')
args = parser.parse_args()

output_file = args.output_file[0]
#print(args.input_file)
if (platform.system() == "Windows"):
    input_file = sorted(glob.glob(args.input_file))[0]
else:
    input_file = args.input_file

sift = cv2.xfeatures2d.SIFT_create()
matcher = cv2.DescriptorMatcher_create("FlannBased")

image = Image.open(input_file)
image.seek(0)
orig_image = numpy.array(image)
(orig_kps, orig_descs) = sift.detectAndCompute(orig_image, None)

shift = pandas.DataFrame({'slice' : 1, \
                         'shiftX': 0.0, 'shiftY': 0.0, 'corr': 0.0}, \
                         index=[1], \
                         columns=['slice', 'shiftX', 'shiftY', 'corr'])

image.seek(0)
frames = ImageSequence.Iterator(image)
next(frames)
plane_index = 2

for frame in frames:
    next_image = numpy.array(frame)
    (next_kps, next_descs) = sift.detectAndCompute(next_image, None)

    result = matcher.match(orig_descs, next_descs)
    sys.exit()
    
    print(plane_index, " +X= ", result[2], " +Y= ", result[1])
    shift_add = pandas.DataFrame({'slice' : plane_index, \
                          'shiftX': result[2], 'shiftY': result[1], 'corr': result[0]}, \
                          index=[plane_index], \
                          columns=['slice', 'shiftX', 'shiftY', 'corr'])
    shift = shift.append(shift_add)
    plane_index = plane_index + 1

shift.to_csv(output_file, index=False, sep='\t')
