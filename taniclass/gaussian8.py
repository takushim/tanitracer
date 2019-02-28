#!/usr/bin/env python

import os, sys, numpy, pandas, time
import scipy.ndimage as ndimage
import scipy.stats as stats
from skimage.feature import peak_local_max

class Gaussian8:
    def __init__ (self):
        self.laplace = 2.0 # Diameter of Spots
        self.min_distance = 1 # Pixel area (int) to find local max (usually 1)
        self.threshold_abs = 0.006 # Threshold to find local max
        self.max_diameter = 10.0
        self.columns = ['total_index', 'plane', 'index', 'x', 'y', 'diameter', 'intensity', 'fit_error', 'chi_square']
        self.image_clip_min = 0.0
        self.image_clip_max = numpy.iinfo(numpy.int32).max

    def output_header (self, output_file, input_filename, image_array):
        filename = os.path.basename(input_filename)
        planes = image_array.shape[0]
        if len(image_array.shape) == 2:
            planes = 1

        #params = {'input_file': filename, 'total_planes': planes, \
        #          'width': image_array.shape[2], 'height': image_array.shape[1], \
        #          'laplace': self.laplace. 'min_distance': self.min_distance, \
        #          'threshold_abs': self.threshold_abs, \
        #          'image_clip_min': self.image_clip_min, 'image_clip_max': self.image_clip_max}

        output_file.write('## Traced by TaniTracer at %s for %s\n' % (time.ctime(), filename))
        output_file.write('#   total_planes = %d; width = %d; height = %d\n' %\
                          (planes, image_array.shape[2], image_array.shape[1]))
        output_file.write('#   laplace = %f; min_distance = %d; threshold_abs = %f\n' %\
                          (self.laplace, self.min_distance, self.threshold_abs))
        output_file.write('#   max_diameter = %f\n' %\
                          (self.max_diameter))
        output_file.write('#   image_clip_min = %f; image_clip_max = %f\n' %\
                          (self.image_clip_min, self.image_clip_max))

    def set_image_clip (self, image_array):
        self.image_clip_min = stats.scoreatpercentile(image_array, 0.1)
        self.image_clip_max = stats.scoreatpercentile(image_array, 99.9)

    def gaussian_fitting (self, input_image, float_image):
        # Find local max at 1-pixel resolution (order: [y, x])
        xy = peak_local_max(float_image, min_distance = self.min_distance,\
                            threshold_abs = self.threshold_abs, exclude_border = True)

        # Calculate subpixel correction (x = xy[:,1], y = xy[:,0])
        c10 = ( - numpy.log(float_image[xy[:,0] - 1, xy[:,1] - 1]) - numpy.log(float_image[xy[:,0], xy[:,1] - 1]) \
                - numpy.log(float_image[xy[:,0] + 1, xy[:,1] - 1]) + numpy.log(float_image[xy[:,0] - 1, xy[:,1] + 1]) \
                + numpy.log(float_image[xy[:,0], xy[:,1] + 1]) + numpy.log(float_image[xy[:,0] + 1, xy[:,1] + 1]) ) / 6
        c01 = ( - numpy.log(float_image[xy[:,0] - 1, xy[:,1] - 1]) - numpy.log(float_image[xy[:,0] - 1, xy[:,1]]) \
                - numpy.log(float_image[xy[:,0] - 1, xy[:,1] + 1]) + numpy.log(float_image[xy[:,0] + 1, xy[:,1] - 1]) \
                + numpy.log(float_image[xy[:,0] + 1, xy[:,1]]) + numpy.log(float_image[xy[:,0] + 1, xy[:,1] + 1]) ) / 6
        c20 = (   numpy.log(float_image[xy[:,0] - 1, xy[:,1] - 1]) + numpy.log(float_image[xy[:,0], xy[:,1] - 1]) \
                + numpy.log(float_image[xy[:,0] + 1, xy[:,1] - 1]) - 2 * numpy.log(float_image[xy[:,0] - 1,xy[:,1]]) \
                - 2 * numpy.log(float_image[xy[:,0], xy[:,1]]) - 2 * numpy.log(float_image[xy[:,0] + 1, xy[:,1]]) \
                + numpy.log(float_image[xy[:,0] - 1, xy[:,1] + 1]) + numpy.log(float_image[xy[:,0], xy[:,1] + 1]) \
                + numpy.log(float_image[xy[:,0] + 1, xy[:,1] + 1]) ) / 6
        c02 = (   numpy.log(float_image[xy[:,0] - 1, xy[:,1] - 1]) + numpy.log(float_image[xy[:,0] - 1,xy[:,1]]) \
                + numpy.log(float_image[xy[:,0] - 1, xy[:,1] + 1]) - 2 * numpy.log(float_image[xy[:,0], xy[:,1] - 1]) \
                - 2 * numpy.log(float_image[xy[:,0], xy[:,1]]) - 2 * numpy.log(float_image[xy[:,0], xy[:,1] + 1]) \
                + numpy.log(float_image[xy[:,0] + 1, xy[:,1] - 1]) + numpy.log(float_image[xy[:,0] + 1,xy[:,1]]) \
                + numpy.log(float_image[xy[:,0] + 1, xy[:,1] + 1]) ) / 6
        c00 = ( - numpy.log(float_image[xy[:,0] - 1, xy[:,1] - 1]) + 2 * numpy.log(float_image[xy[:,0], xy[:,1] - 1]) \
                - numpy.log(float_image[xy[:,0] + 1, xy[:,1] - 1]) + 2 * numpy.log(float_image[xy[:,0] - 1,xy[:,1]]) \
                + 5 * numpy.log(float_image[xy[:,0], xy[:,1]]) + 2 * numpy.log(float_image[xy[:,0] + 1, xy[:,1]]) \
                - numpy.log(float_image[xy[:,0] - 1, xy[:,1] + 1]) + 2 * numpy.log(float_image[xy[:,0], xy[:,1] + 1]) \
                - numpy.log(float_image[xy[:,0] + 1, xy[:,1] + 1]) ) / 9

        fit_error = ( c00 - c10 + c20 - c01 + c02 - numpy.log(float_image[xy[:,0] - 1, xy[:,1] - 1]) )**2 \
            + ( c00 - c10 + c20 - numpy.log(float_image[xy[:,0], xy[:,1] - 1]) )**2 \
            + ( c00 - c10 + c20 + c01 + c02 - numpy.log(float_image[xy[:,0] + 1, xy[:,1] - 1]) )**2 \
            + ( c00 - c01 + c02 - numpy.log(float_image[xy[:,0] - 1, xy[:,1]]) )**2 \
            + ( c00 - numpy.log(float_image[xy[:,0], xy[:,1]]) )**2 \
            + ( c00 + c01 + c02 - numpy.log(float_image[xy[:,0] + 1, xy[:,1]]) )**2 \
            + ( c00 + c10 + c20 - c01 + c02 - numpy.log(float_image[xy[:,0] - 1, xy[:,1] + 1]) )**2 \
            + ( c00 + c10 + c20 - numpy.log(float_image[xy[:,0], xy[:,1] + 1]) )**2 \
            + ( c00 + c10 + c20 + c01 + c02 - numpy.log(float_image[xy[:,0] + 1, xy[:,1] + 1]) )**2

        chi_square = ( c00 - c10 + c20 - c01 + c02 - numpy.log(float_image[xy[:,0] - 1, xy[:,1] - 1]) )**2 / numpy.abs(numpy.log(float_image[xy[:,0] - 1, xy[:,1] - 1])) \
                   + ( c00 - c10 + c20 - numpy.log(float_image[xy[:,0], xy[:,1] - 1]) )**2 / numpy.abs(numpy.log(float_image[xy[:,0], xy[:,1] - 1])) \
                   + ( c00 - c10 + c20 + c01 + c02 - numpy.log(float_image[xy[:,0] + 1, xy[:,1] - 1]) )**2  / numpy.abs(numpy.log(float_image[xy[:,0] + 1, xy[:,1] - 1])) \
                   + ( c00 - c01 + c02 - numpy.log(float_image[xy[:,0] - 1, xy[:,1]]) )**2  / numpy.abs(numpy.log(float_image[xy[:,0] - 1, xy[:,1]])) \
                   + ( c00 - numpy.log(float_image[xy[:,0], xy[:,1]]) )**2  / numpy.abs(numpy.log(float_image[xy[:,0], xy[:,1]])) \
                   + ( c00 + c01 + c02 - numpy.log(float_image[xy[:,0] + 1, xy[:,1]]) )**2  / numpy.abs(numpy.log(float_image[xy[:,0] + 1, xy[:,1]])) \
                   + ( c00 + c10 + c20 - c01 + c02 - numpy.log(float_image[xy[:,0] - 1, xy[:,1] + 1]) )**2  / numpy.abs(numpy.log(float_image[xy[:,0] - 1, xy[:,1] + 1])) \
                   + ( c00 + c10 + c20 - numpy.log(float_image[xy[:,0], xy[:,1] + 1]) )**2  / numpy.abs(numpy.log(float_image[xy[:,0], xy[:,1] + 1])) \
                   + ( c00 + c10 + c20 + c01 + c02 - numpy.log(float_image[xy[:,0] + 1, xy[:,1] + 1]) )**2  / numpy.abs(numpy.log(float_image[xy[:,0] + 1, xy[:,1] + 1]))

        x = xy[:,1] - 0.5 * (c10/c20)
        y = xy[:,0] - 0.5 * (c01/c02)
        diameter = 2 * numpy.sqrt(- (0.5/c20 + 0.5/c02) / 2)
        intensity = input_image[xy[:,0], xy[:,1]]

        error_dict = {}

        # omit nan spots
        last_spots = len(xy)
        indexes = numpy.ones(len(xy), dtype=numpy.bool)
        indexes = indexes & (x >= 0) & (x <= float_image.shape[1])
        indexes = indexes & (y >= 0) & (y <= float_image.shape[0])
        error_dict['nan'] = last_spots - numpy.sum(indexes)
        last_spots = numpy.sum(indexes)

        # omit spots of abnormal subpixel correction
        indexes = indexes & ((0.5 * (c10/c20)) < 1)
        indexes = indexes & ((0.5 * (c01/c02)) < 1)
        error_dict['large_shift'] = last_spots - numpy.sum(indexes)
        last_spots = numpy.sum(indexes)

        # omit spots of large diameter
        indexes = indexes & (diameter <= self.max_diameter)
        error_dict['diameter'] = last_spots - numpy.sum(indexes)
        last_spots = numpy.sum(indexes)

        # omit duplicated spots
        indexes = indexes & (aaaa)
        error_dict['duplicate'] = last_spots - numpy.sum(indexes)
        last_spots = numpy.sum(indexes)

        # make result dictionary
        x = x[indexes]
        y = y[indexes]
        fit_error = fit_error[indexes]
        chi_square = chi_square[indexes]
        diameter = diameter[indexes]
        intensity = intensity[indexes]

        result_dict = {'x': x, 'y': y, 'fit_error': fit_error, 'chi_square': chi_square, 'diameter': diameter, 'intensity': intensity}

        return result_dict, error_dict

    def clip_array (self, float_array):
        return float_array.clip(self.image_clip_min, self.image_clip_max)

    def standardize_and_filter_image (self, float_image):
        float_image = - (float_image - numpy.max(float_image)) / numpy.ptp(float_image)
        return ndimage.gaussian_laplace(float_image, self.laplace)

    def convert_to_pandas (self, result):
        length = max([len(item) for item in result.values()])
        result.update({'total_index' : numpy.arange(length)})
        return pandas.DataFrame(result, columns = self.columns)

    def fitting_image_array (self, input_image):
        numpy.seterr(divide='ignore', invalid='ignore')

        # get float image anf filter
        float_image = numpy.array(input_image, 'f')
        float_image = self.clip_array(float_image)
        float_image = self.standardize_and_filter_image(float_image)

        # fitting
        result, error = self.gaussian_fitting(input_image, float_image)

        # report error
        print("Dropped spots: %d by nan, %d by large_shift, %d by diameter" % \
              (error['nan'], error['large_shift'], error['diameter']))

        # Make Pandas dataframe
        length = max([len(item) for item in result.values()])
        result.update({'plane': numpy.full(length, 0), 'index': numpy.arange(length)})
        spot_table = self.convert_to_pandas(result)

        return spot_table

    def fitting_image_stack (self, input_stack):
        numpy.seterr(divide='ignore', invalid='ignore')

        # get float image anf filter
        float_stack = numpy.array(input_stack, 'f')
        float_stack = self.clip_array(float_stack)

        # arrays to store results
        result_array = []
        error_array = []

        for index in range(len(input_stack)):
            # filter and fitting
            float_stack[index] = self.standardize_and_filter_image(float_stack[index])
            result, error = self.gaussian_fitting(input_stack[index], float_stack[index])

            # add plane and index
            length = max([len(item) for item in result.values()])
            result.update({'plane': numpy.full(length, index), 'index': numpy.arange(length)})

            # append to arrays
            result_array.append(result)
            error_array.append(error)

        # accumulate result
        result_concat = {}
        for key in result_array[0].keys():
            result_concat[key] = numpy.concatenate([result[key] for result in result_array])

        # sum error spots
        error_sum = {}
        for key in error_array[0].keys():
            error_sum[key] = numpy.sum([error[key] for error in error_array])
        print("Dropped spots: %d by nan, %d by large_shift, %d by diameter" % \
              (error_sum['nan'], error_sum['large_shift'], error_sum['diameter']))

        # make pandas table
        spot_table = self.convert_to_pandas(result_concat)
        spot_table['total_index'] = numpy.arange(len(spot_table))
        return spot_table
