#!/usr/bin/env python

import sys, numpy, pandas

class SpotFilter:
    def __init__ (self):
        self.lifetime_min = 0
        self.lifetime_max = numpy.inf

    def filter_spots_lifetime (self, spot_table):
        spot_table = spot_table.sort_values(by = ['total_index', 'plane']).reset_index(drop=True)
        
        if ('lifetime' in spot_table.columns) is False:
            spot_table = self.calculate_lifetime(spot_table)
                
        spot_table = spot_table[(self.lifetime_min <= spot_table.lifetime) & \
                                (spot_table.lifetime <= self.lifetime_max)].reset_index(drop=True)
        
        return spot_table

    def omit_lastplane_spots (self, spot_table, lastplane_index):
        total_indexes = spot_table[spot_table.plane == lastplane_index].total_index.tolist()
        total_indexes = list(set(total_indexes))
        #print(total_indexes)
        
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

    def calculate_lifetime (self, spot_table):
        if ('lifecount' in spot_table.columns) is False:
            spot_table['lifecount'] = (spot_table.groupby('total_index').cumcount() + 1)

        if ('lifetime' in spot_table.columns) is False:
            lifetime_table = spot_table['total_index'].value_counts().to_frame('lifetime')
            spot_table = pandas.merge(spot_table, lifetime_table, \
                                      left_on='total_index', right_index=True, how='left')

        return spot_table

