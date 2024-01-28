#!/usr/bin/env python

import sys, time, numpy, tifffile

class SpotFilter:
    def __init__ (self):
        self.lifetime_min = 0
        self.lifetime_max = numpy.inf
        self.mask_image_filename = None

    def output_header (self, output_file):
        output_file.write('## Filtered by SpotFilter at %s\n' % (time.ctime()))
        output_file.write('#   mask_image = %s\n' % (self.mask_image_filename))

    def filter_spots_lifetime (self, spot_table):
        spot_table = spot_table.sort_values(by = ['total_index', 'plane']).reset_index(drop=True)
        spot_table = spot_table[(self.lifetime_min <= spot_table.life_total) & \
                                (spot_table.life_total <= self.lifetime_max)].reset_index(drop=True)

        return spot_table

    def omit_lastplane_spots (self, spot_table, lastplane_index):
        total_indexes = spot_table[spot_table.plane == lastplane_index].total_index.tolist()
        total_indexes = list(set(total_indexes))

        return spot_table[~spot_table.total_index.isin(total_indexes)]

    def keep_first_spots (self, spot_table):
        spot_table = spot_table.drop_duplicates(subset='total_index', keep='first').reset_index(drop=True)
        return spot_table

    def keep_last_spots (self, spot_table):
        spot_table = spot_table.drop_duplicates(subset='total_index', keep='last').reset_index(drop=True)
        return spot_table

    def average_spots (self, spot_table):
        agg_dict = {x : numpy.max for x in spot_table.columns}
        agg_dict['x'] = numpy.mean
        agg_dict['y'] = numpy.mean
        agg_dict['intensity'] = numpy.mean
        agg_dict['distance'] = numpy.sum
        spot_table = spot_table.groupby('total_index').agg(agg_dict).reset_index(drop=True)
        return spot_table

    def filter_spots_maskimage (self, spot_table):
        if self.mask_image_filename is None:
            return spot_table

        mask_image = tifffile.imread(self.mask_image_filename)
        mask_image = mask_image.astype(bool).astype(numpy.uint8)

        first_spot_table = spot_table.drop_duplicates(subset='total_index', keep='first').reset_index(drop=True)
        first_spot_table['mask'] = mask_image[first_spot_table.y.values.astype(int), first_spot_table.x.values.astype(int)]
        index_set = set(first_spot_table[first_spot_table['mask'] > 0].total_index.to_list())

        return spot_table[spot_table.total_index.isin(index_set)]


