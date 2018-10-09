#!/usr/bin/env python

import sys, numpy, pandas, time
import cv2

class Akaze:
    def __init__ (self):
        self.columns = ['align_plane', 'align_x', 'align_y']
        self.threshold = 0.00005
        self.matching_ratio = 0.15

    def output_header (self, output_file, input_filename, reference_filename):
        output_file.write('## Alignment by TaniAlign (AKAZE) at %s\n' % (time.ctime()))
        output_file.write('#   file = \'%s\'; reference = %s\n' % (input_filename, reference_filename))
        output_file.write('#   threshold = %f; matching_ratio = %f\n' % (self.threshold, self.matching_ratio))

    def convert_to_uint8 (self, orig_image):
        images_uint8 = numpy.zeros(orig_image.shape, dtype = numpy.uint8)

        image_type = orig_image.dtype.name
        if image_type == 'int32' or image_type == 'uint32' or image_type == 'uint16':
            mean = numpy.mean(orig_image)
            sigma = numpy.std(orig_image)
            image_min = max(0, mean - 3 * sigma)
            image_max = min(mean + 4 * sigma, numpy.iinfo(orig_image.dtype).max)
            images_uint8 = (255.0 * (orig_image - image_min) / (image_max - image_min)).clip(0, 255).astype(numpy.uint8)
        elif image_type == 'uint8':
            images_uint8 = orig_image
        else:
            raise Exception('invalid image file format')

        return images_uint8

    def calculate_alignments (self, orig_images, reference = None):
        detector = cv2.AKAZE_create(threshold = self.threshold)

        # array for the results
        move_x = numpy.zeros(len(orig_images))
        move_y = numpy.zeros(len(orig_images))

        # params of original image
        if reference is not None:
            (orig_kps, orig_descs) = detector.detectAndCompute(reference, None)
        else:
            (orig_kps, orig_descs) = detector.detectAndCompute(orig_images[0], None)

        for index in range(len(orig_images)):
            # params of image
            (this_kps, this_descs) = detector.detectAndCompute(orig_images[index], None)

            # brute-force matching
            matcher = cv2.DescriptorMatcher_create(cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING)
            matches = matcher.match(orig_descs, this_descs, None)
            matches.sort(key = lambda x: x.distance, reverse = False)
            matches = matches[:(int(len(matches) * self.matching_ratio))]

            # calculate the movements of matching points
            orig_points = numpy.zeros((len(matches), 2), dtype = numpy.float32)
            this_points = numpy.zeros((len(matches), 2), dtype = numpy.float32)
            for i, match in enumerate(matches):
                orig_points[i, :] = orig_kps[match.queryIdx].pt
                this_points[i, :] = this_kps[match.trainIdx].pt

            # reduce error matching by RANSAC
            h, mask = cv2.findHomography(orig_points, this_points, cv2.RANSAC, 3.0)
            matches_mask = mask.ravel().tolist() # does this need?

            # calculate the drift
            mvx=0
            mvy=0
            cnt=0
            for k, v in enumerate(mask):
                if v==1:
                    mvx += this_points[k][0] - orig_points[k][0]
                    mvy += this_points[k][1] - orig_points[k][1]
                    cnt += 1
            mvx = mvx / cnt
            mvy = mvy / cnt
            print("Plane %d, dislocation = (%f, %f)." % (index, mvx, mvy))

            move_x[index] = mvx
            move_y[index] = mvy

        # make pandas dataframe
        result = pandas.DataFrame({ \
                'align_plane' : numpy.arange(len(orig_images)), \
                'align_x' : move_x, \
                'align_y' : move_y})

        return result[self.columns]
