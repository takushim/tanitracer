#!/usr/bin/env python

import sys, numpy, pandas, time
import cv2

class AlignSift:
    def __init__ (self):
        self.columns = ['plane', 'x', 'y']
        self.matching_ratio = 0.6
        
    def output_header (self, output_file, input_filename, reference_filename):
        output_file.write('## Alignment by TaniAligner at %s\n' % (time.ctime()))
        output_file.write('#   file = "%s"; reference = %s\n' % (input_filename, reference_filename))
        output_file.write('#   matching_ratio = %f\n' % (self.matching_ratio))
        
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

    def calculate_alignments (self, images_uint8, reference_uint8 = None):
        sift = cv2.xfeatures2d.SIFT_create()
        matcher = cv2.BFMatcher()
        
        # array for results
        move_x = numpy.zeros(len(images_uint8))
        move_y = numpy.zeros(len(images_uint8))
        
        # params of original image
        if reference_uint8 is not None:
            (orig_kps, orig_descs) = sift.detectAndCompute(reference_uint8, None)
        else:
            (orig_kps, orig_descs) = sift.detectAndCompute(images_uint8[0], None)
        
        for index in range(len(images_uint8)):
            # params of image
            (kps, descs) = sift.detectAndCompute(images_uint8[index], None)
            
            # brute-force matching
            matches = matcher.knnMatch(orig_descs ,descs, k = 2)
            good_matches = [m for m, n in matches if m.distance < self.matching_ratio * n.distance]

            # calculate mean vectors
            mvx, mvy = self.mean_of_vectors(orig_kps, kps, good_matches)
            print("Plane %d, dislocation = (%f, %f)." % (index, mvx, mvy))
            
            move_x[index] = mvx
            move_y[index] = mvy
            
        # make pandas dataframe
        result = pandas.DataFrame({ \
                'plane' : numpy.arange(len(images_uint8)), \
                'x' : move_x, \
                'y' : move_y})

        return result[self.columns]
            
    def mean_of_vectors(self, kp1, kp2, good):
        l = len(good)
        svx = 0
        svy = 0
        for mat in good:
            img1_idx = mat.queryIdx
            img2_idx = mat.trainIdx
            (x1,y1) = kp1[img1_idx].pt
            (x2,y2) = kp2[img2_idx].pt
            svx += x2-x1
            svy += y2-y1
        mvx = svx/l
        mvy = svy/l

        return mvx, mvy
    
