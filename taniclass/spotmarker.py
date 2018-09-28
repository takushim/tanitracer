#!/usr/bin/env python

import sys, pandas, numpy
from PIL import Image, ImageDraw

class SpotMarker:
    def __init__ (self):
        self.marker_size = 6
        self.mark_emerge = False
        self.drop_new_in_first = False
        self.marker_colors = ['red', 'orange', 'blue', 'cyan']
        self.rainbow_colors = ["red", "blue", "lightgreen", "magenta", "purple", "cyan",\
                               "yellow", "orange", "maroon"]

    def convert_to_color (self, orig_image):

        image_color = numpy.zeros(orig_image.shape + (3,), dtype = numpy.uint8)

        image_type = orig_image.dtype.name
        if image_type == 'int32' or image_type == 'uint16':
            mean = numpy.mean(orig_image)
            sigma = numpy.std(orig_image)
            image_min = max(0, mean - 3 * sigma)
            image_max = min(mean + 4 * sigma, numpy.iinfo(orig_image.dtype).max)
            image_8bit = (255.0 * (orig_image - image_min) / (image_max - image_min)).clip(0, 255).astype(numpy.uint8)
            image_color[:,:,:,0] = image_color[:,:,:,1] = image_color[:,:,:,2] = image_8bit
        elif image_type == 'uint8':
            image_color[:,:,:,0] = image_color[:,:,:,1] = image_color[:,:,:,2] = orig_image
        else:
            raise Exception('invalid image file format')

        return image_color

    def tracking_status (self, spot_table):
        total_indexes = spot_table.total_index.tolist()

        status = ['cont' for i in range(len(total_indexes))]
        status[0] = 'new'

        for i in range(len(status) - 1):
            if total_indexes[i] < total_indexes[i + 1]:
                #print(total_indexes[i], total_indexes[i+1])
                if status[i] == 'new':
                    status[i], status[i + 1] = 'one', 'new'
                else:
                    status[i], status[i + 1] = 'end', 'new'
        if status[-1] == 'new':
            status[-1] = 'one'
        else:
            status[-1] = 'end'

        return status

    def mark_rainbow_spots (self, image_color, spot_table):
        # copy for working
        work_table = spot_table.copy()
        statuses = self.tracking_status(work_table)
        work_table['status'] = statuses

        # draw markers
        for index in range(len(image_color)):
            spots = work_table[work_table.plane == index].reset_index(drop=True)

            if len(spots) == 0:
                print("Skipped plane %d with %d spots." % (index, len(spots)))
                continue

            spots['int_x'] = spots['x'].astype(numpy.int)
            spots['int_y'] = spots['y'].astype(numpy.int)
            spots = spots.sort_values(by = ['int_x', 'int_y']).reset_index(drop=True)

            # check possible error spots (duplicated)
            spots['duplicated'] = spots.duplicated(subset = ['int_x', 'int_y'], keep = False)
            error_spots = len(spots[spots['duplicated'] == True])
            if error_spots > 0:
                print("Possible %d duplicated spots in plane %d." % (error_spots, index))

            image = Image.fromarray(image_color[index])
            draw = ImageDraw.Draw(image)

            for row, spot in spots.iterrows():
                # draw marker
                draw.ellipse(((spot.int_x - self.marker_size, spot.int_y - self.marker_size),\
                              (spot.int_x + self.marker_size, spot.int_y + self.marker_size)),\
                              fill = None, outline = self.rainbow_colors[spot.total_index % len(self.rainbow_colors)])
                # mark emerging spot
                if self.mark_emerge is True:
                    if spot['status'] == 'new' or spot['status'] == 'one':
                        if self.drop_new_in_first is False or spot['plane'] > 0:
                            marker_size = int(self.marker_size * 1.5)
                            draw.ellipse(((spot.int_x - marker_size, spot.int_y - marker_size),\
                                          (spot.int_x + marker_size, spot.int_y + marker_size)),\
                                          fill = None, outline = self.rainbow_colors[spot.total_index % len(self.rainbow_colors)])

            # save image
            image_color[index] = numpy.asarray(image)

        return image_color

    def mark_spots (self, image_color, spot_table):
        # mark new, cont, end
        marker_color_new = self.marker_colors[0]
        marker_color_cont = self.marker_colors[1]
        marker_color_end = self.marker_colors[2]

        statuses = self.tracking_status(spot_table)

        # make color list
        if set(statuses) == {'one'}:
            colors = [marker_color_new for i in range(len(statuses))]
        else:
            colors = [marker_color_cont for i in range(len(statuses))]
            colors = [marker_color_new if statuses[i] == 'new' else colors[i] for i in range(len(colors))]
            colors = [marker_color_end if statuses[i] == 'end' else colors[i] for i in range(len(colors))]
            colors = [marker_color_new if statuses[i] == 'one' else colors[i] for i in range(len(colors))]

        # copy for working
        work_table = spot_table.copy()
        work_table['status'] = statuses
        work_table['color'] = colors

        # draw markers
        for index in range(len(image_color)):
            spots = work_table[work_table.plane == index].reset_index(drop=True)

            if len(spots) == 0:
                print("Skipped plane %d with %d spots." % (index, len(spots)))
                continue

            spots['int_x'] = spots['x'].astype(numpy.int)
            spots['int_y'] = spots['y'].astype(numpy.int)
            spots = spots.sort_values(by = ['int_x', 'int_y']).reset_index(drop=True)

            # check possible error spots (duplicated)
            spots['duplicated'] = spots.duplicated(subset = ['int_x', 'int_y'], keep = False)
            error_spots = len(spots[spots['duplicated'] == True])
            if error_spots > 0:
                print("Possible %d duplicated spots in plane %d." % (error_spots, index))

            image = Image.fromarray(image_color[index])
            draw = ImageDraw.Draw(image)

            for row, spot in spots.iterrows():
                # draw marker
                if self.drop_new_in_first is True and spot['plane'] == 0:
                    draw.ellipse(((spot.int_x - self.marker_size, spot.int_y - self.marker_size),\
                                  (spot.int_x + self.marker_size, spot.int_y + self.marker_size)),\
                                  fill = None, outline = marker_color_cont)
                else:
                    draw.ellipse(((spot.int_x - self.marker_size, spot.int_y - self.marker_size),\
                                  (spot.int_x + self.marker_size, spot.int_y + self.marker_size)),\
                                  fill = None, outline = spot.color)

                # draw additional marker
                if spot['status'] == 'one':
                    draw.arc(((spot.int_x - self.marker_size, spot.int_y - self.marker_size),\
                              (spot.int_x + self.marker_size, spot.int_y + self.marker_size)),\
                              315, 135, fill = marker_color_end)

                # draw new spots
                if self.mark_emerge is True:
                    if self.drop_new_in_first is False or spot['plane'] > 0:
                        if spot['status'] == 'new' or spot['status'] == 'one':
                            marker_size = int(self.marker_size * 1.5)
                            draw.ellipse(((spot.int_x - marker_size, spot.int_y - marker_size),\
                                          (spot.int_x + marker_size, spot.int_y + marker_size)),\
                                          fill = None, outline = self.marker_colors[0])

                # mark duplicated spot
                if spot['duplicated'] is True:
                    draw.ellipse(((spot.int_x - self.marker_size + 1, spot.int_y - self.marker_size + 1),\
                                  (spot.int_x + self.marker_size + 1, spot.int_y + self.marker_size + 1)),\
                                fill = None, outline = self.marker_colors[3])

            image_color[index] = numpy.asarray(image)

        return image_color
