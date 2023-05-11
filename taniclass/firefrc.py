#!/usr/bin/env python

# Copyright (c) 2018-2019, Takushi Miyoshi
# Copyright (c) 2012-2019, Department of Otolaryngology, 
#                          Graduate School of Medicine, Kyoto University
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# This fils is written by Takushi Miyoshi referring to the algorhythm in:
# - spin_average.py
# - fourier_ring_corr.py
# by Sajid Ari (https://github.com/s-sajid-ali/FRC)

import sys, numpy
import statsmodels.nonparametric.smoothers_lowess as smoothers_lowess

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

        indexes = numpy.round(numpy.sqrt(y_grid * y_grid + x_grid * x_grid)).astype(int)
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
        spin_12 = self.spin_average(numpy.multiply(image_fft1, numpy.conj(image_fft2)))
        spin_11 = self.spin_average(numpy.multiply(image_fft1, numpy.conj(image_fft1)))
        spin_22 = self.spin_average(numpy.multiply(image_fft2, numpy.conj(image_fft2)))

        fsc = numpy.abs(spin_12) / numpy.sqrt(numpy.abs(spin_11 * spin_22))
        sf = 2 * numpy.arange(numpy.shape(spin_12)[0]) / numpy.shape(image_array1)[0]

        return sf, fsc

    def smoothing_fsc (self, sf, fsc):
        return smoothers_lowess.lowess(fsc, sf, frac = 0.1, return_sorted = False)

    def intersection_threshold (self, sf, smooth_fsc, threshold = 0.1427):
        fsc_sub = smooth_fsc - threshold
        cross_indexes = numpy.where(numpy.diff(numpy.sign(fsc_sub)) != 0)[0]

        sf_sections = numpy.array([[sf[i], sf[i+1]] for i in cross_indexes])
        fsc_sub_sections = numpy.array([[fsc_sub[i], fsc_sub[i+1]] for i in cross_indexes])

        sf_crosses = []
        for index in range(len(sf_sections)):
            sf_cross = sf_sections[index][0] - fsc_sub_sections[index][0] * \
                      (sf_sections[index][1] - sf_sections[index][0]) / \
                      (fsc_sub_sections[index][1] - fsc_sub_sections[index][0])
            sf_crosses.append(sf_cross)

        return numpy.array(sf_crosses)
