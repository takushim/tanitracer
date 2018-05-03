#!/usr/bin/env python

import sys, numpy, pandas, time
from sklearn.neighbors import NearestNeighbors

class NNChaser:
    def __init__ (self):
        self.chase_distance = 3.5
        
    def output_header (self, output_file):
        output_file.write('## Chased by TaniChaser at %s\n' % (time.ctime()))
        output_file.write('#   chase_distance = %f\n' % (self.chase_distance))
    
    def chase_spots (self, spot_table):
        numpy.set_printoptions(threshold=numpy.inf)
        results = []
        
        for index in range(max(spot_table.plane)):
            # get partial spot table
            orig_spots = spot_table[spot_table.plane == index]
            next_spots = spot_table[spot_table.plane == index + 1]
            if (len(orig_spots) == 0) or (len(next_spots) == 0):
                results.append(numpy.array([]))
                continue
            
            # nearest neighbor to find nearest spots
            nn = NearestNeighbors(n_neighbors = 1, metric = 'euclidean').fit(next_spots[['x', 'y']].values)
            distances, targets = nn.kneighbors(orig_spots[['x', 'y']].values)
            
            # make numpy array to find duplicates and too far spots
            pairs = numpy.zeros(len(orig_spots), dtype=[('orig_array_index', numpy.int), \
                                                        ('orig_total_index', numpy.int), \
                                                        ('next_array_index', numpy.int), \
                                                        ('distance', numpy.float), \
                                                        ('valid', numpy.bool)])
            pairs['orig_array_index'] = numpy.arange(len(orig_spots))
            pairs['orig_total_index'] = orig_spots.total_index.values
            pairs['next_array_index'] = targets.flatten()
            pairs['distance'] = distances.flatten()
            pairs['valid'] = True
            
            # omit too far spots
            pairs['valid'][pairs['distance'] > self.chase_distance] = False
            
            # find duplicated targets
            pairs = numpy.sort(pairs, order=['next_array_index', 'distance'])
            unique_index = numpy.unique(pairs['next_array_index'], return_index = True)[1]
            # omit duplicates
            mask = numpy.ones(len(pairs), dtype=numpy.bool)
            mask[unique_index] = False
            pairs['valid'][mask] = False
                        
            # delete next_index and distance
            pairs['next_array_index'][pairs['valid'] == False] = -1
            pairs['distance'][pairs['valid'] == False] = 0.0
            
            # sort again and save
            pairs = numpy.sort(pairs, order=['orig_array_index'])
            results.append(pairs)

        # add last results
        lastplane_spots = spot_table[spot_table.plane == max(spot_table.plane)]
        pairs = numpy.zeros(len(lastplane_spots), dtype=[('orig_array_index', numpy.int), \
                                                         ('orig_total_index', numpy.int), \
                                                         ('next_array_index', numpy.int), \
                                                         ('distance', numpy.float), \
                                                         ('valid', numpy.bool)])
        pairs['orig_array_index'] = numpy.arange(len(lastplane_spots))
        pairs['orig_total_index'] = lastplane_spots.total_index.values
        pairs['next_array_index'] = -1
        pairs['distance'] = 0.0
        pairs['valid'] = False
        results.append(pairs)
        
        # chase spots by updating total_index
        for index in range(max(spot_table.plane)):
            orig_pairs = results[index]
            next_pairs = results[index + 1]
            if (len(orig_pairs) == 0) or (len(next_pairs) == 0):
                continue
            
            orig_indexes = orig_pairs['orig_array_index'][orig_pairs['valid'] == True]
            next_indexes = orig_pairs['next_array_index'][orig_indexes]
            next_pairs['orig_total_index'][next_indexes] = orig_pairs['orig_total_index'][orig_indexes]
        
        # shift distances
        for index in reversed(range(max(spot_table.plane))):
            orig_pairs = results[index]
            next_pairs = results[index + 1]
            if (len(orig_pairs) == 0) or (len(next_pairs) == 0):
                continue

            orig_indexes = orig_pairs['orig_array_index'][orig_pairs['valid'] == True]
            next_indexes = orig_pairs['next_array_index'][orig_indexes]
            next_pairs['distance'][next_indexes] = orig_pairs['distance'][orig_indexes]
            
            mask = numpy.ones(len(next_pairs), dtype=numpy.bool)
            mask[next_indexes] = False
            next_pairs['distance'][mask] = 0.0
        results[0]['distance'] = 0.0
            
        # make new columns
        spot_table['total_index'] = numpy.concatenate([result['orig_total_index'] for result in results])
        spot_table['distance'] = numpy.concatenate([result['distance'] for result in results])
        
        return spot_table.sort_values(by = ['total_index', 'plane']).reset_index(drop=True)

