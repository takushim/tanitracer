#!/usr/bin/env python

import sys, numpy

class FireFRC:
    def __init__ (self):
        pass
        
    def spin_average (self, fft_image):
        #numpy.set_printoptions(threshold=numpy.inf)
        
        shape = numpy.shape(fft_image)
        if len(shape) != 2:
            raise Exception('input_image must be 2d image array')
        
        height, width = shape
        x = numpy.arange(width) - numpy.floor(width / 2)
        y = numpy.arange(height) - numpy.floor(height / 2)
        
        [y_grid, x_grid] = numpy.meshgrid(y, x)
        
        indexes = numpy.round(numpy.sqrt(y_grid * y_grid + x_grid * x_grid)).astype(numpy.int)
        fft_sum = numpy.zeros(numpy.max(indexes) + 1, dtype = numpy.complex)
        fft_count = numpy.zeros(numpy.max(indexes) + 1, dtype = numpy.complex )

        for index in range(numpy.max(indexes) + 1):
            array_to_apply = numpy.where(indexes == index)
            fft_sum[index] = numpy.sum(fft_image[array_to_apply])
            fft_count[index] = numpy.shape(array_to_apply)[1]
        
        return fft_sum / fft_count

    def fourier_spin_correlation (self, image_array1, image_array2):
        if numpy.shape(image_array1) != numpy.shape(image_array1):
            raise Exception('input images must have the same dimensions')

        if numpy.shape(image_array1)[0] != numpy.shape(image_array1)[1]:
            raise Exception('input images must be squares')

        image_fft1 = numpy.fft.fftshift(numpy.fft.fft2(image_array1))
        image_fft2 = numpy.fft.fftshift(numpy.fft.fft2(image_array2))

        #I1 and I2 store the DFT of the images to be used in the calcuation for the FSC
        spin_averages_12  = self.spin_average(numpy.multiply(image_fft1,numpy.conj(image_fft2)))
        spin_averages_11 = self.spin_average(numpy.multiply(image_fft1,numpy.conj(image_fft1)))
        spin_averages_22 = self.spin_average(numpy.multiply(image_fft2,numpy.conj(image_fft2)))
        
        fsc = numpy.abs(spin_averages_12) / numpy.sqrt(numpy.abs(numpy.multiply(spin_averages_11, spin_averages_22)))
        sf_nyq = 2 * numpy.arange(numpy.shape(spin_averages_12)[0]) / numpy.shape(image_array1)[0]

        return sf_nyq, fsc

