#!/usr/bin/env python

import os, sys, datetime
import numpy, pandas
import tifffile

class SpotPlotter:
    def __init__ (self):
        self.orig_width = None
        self.orig_height = None
        self.scale = 4
        self.align_each = 500

    def plot_spots (self, spot_table, image_array):
