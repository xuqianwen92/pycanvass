import numpy as np
# from mpl_toolkits.basemap import Basemap
# import matplotlib.pyplot as plt
import subprocess
import sys
import re
import os
import pycanvass.utilities as util
import random


def view_on_a_map(filename,**kwargs):
    """
    Plots a feeder file on a map
    :param filename:
    :param kwargs:
    :return:
    """
    if kwargs is not None:
        for key, value in kwargs.iteritems():
            if key == "location":
                location = value
            elif key == "location_latlong":
                location_latlong = value
            elif key == "radius":
                radius = value
            elif key == "basemap":
                basemap = value


def _next_geo_coordinate(geo_coord, distance):
    """
    Calculates the next geo-coordinate.
    If we know one geo-coordinate and how far the coordinate is supposed to be, we can make a random guess about the next co-ordinate point.
    :param geo_coord: tuple containing [lat, long]
    :param distance: in feet.
    :return: next_geo_coord tuple containing [lat, long]

    Note:
    - 1 deg latitude = 111.32 km
    - 1 ft = 0.0003048 km
    - 1 ft = 2.7380524e-6 deg latitude shift

    """
    theta = random.randrange(0, 359)

    if distance != "None":
        horizontal_shift = float(distance) * np.cos(theta)
        vertical_shift = float(distance) * np.sin(theta)
        next_lat = geo_coord[0] + 2.7380524e-6 * vertical_shift
        next_long = geo_coord[1] + horizontal_shift/np.cos(next_lat * (np.pi/180))

        return [next_lat, next_long]


def layout_model(file_or_folder_name, map_random = False):
    """
    
    """
    try:
        # _hide_terminal_output()
        if not os.path.exists('C:\\Program Files (x86)\\Graphviz2.38\\bin'):
            print("[x] Dependency Error: Graphviz is not installed.")
            print("[i] Layout of the GridLAB-D Models will not proceed.")
            print("[i] Please refer to documentation on how to get Graphviz, and set path correctly")
            return
    except Exception:
        
        print("[i] Please refer to documentation")
        
        return 

    if os.path.isfile(file_or_folder_name):
        temp = os.path.basename(file_or_folder_name)
        filename = os.path.splitext(temp)[0]
        file_extension = os.path.splitext(temp)[1]

        if file_extension == ".glm":

            infile = open(file_or_folder_name, 'r')
            outfile = open(filename, 'w')
            lines = infile.readlines()

            # .dot files begin with the 'graph' keyword.
            outfile.write("digraph {\n")
            outfile.write("node [shape=box]\n")
            # These are state variables.  There is no error checking, so we rely on
            # well formatted *.GLM files.
            s = 0
            state = 'start'
            edge_color = 'black'
            edge_style = 'solid'
            lengthVal = 'None'
            lineLengthIncrement = 0

            # Loop through each line in the input file...
            while s < len(lines):
                # Discard Comments
                if re.match("//", lines[s]) == None:
                    if re.search("from", lines[s]) != None:
                        ts = lines[s].split()
                        # Graphvis format can't handle '-' characters, so they are converted to '_'
                        ns = ts[1].rstrip(';').replace('-', '_').replace(':', '_')
                        outfile.write(ns)
                        state = 'after_from'
                    elif state == 'after_from' and re.search("to ", lines[s]) != None:
                        ts = lines[s].split()
                        ns = ts[1].rstrip(';').replace('-', '_').replace(':', '_')
                        if edge_color == 'red':
                            outfile.write(
                                ' -> ' + ns + '[style=' + edge_style + ' color=' + edge_color + ' label="' + lengthVal + '"]\n')
                            outfile.write("node [shape=box]\n")
                        else:
                            outfile.write(
                                ' -> ' + ns + '[style=' + edge_style + ' color=' + edge_color + ' label="' + lengthVal + '"]\n')
                        lengthVal = 'None'
                        # After an edge is added to the graph, reset the states back to default
                        state = 'start'
                        edge_color = 'black'
                        edge_style = 'solid'
                    elif (re.search("object underground_line", lines[s]) is not None) or (
                        re.search("object overhead_line", lines[s]) is not None):
                        while '}' not in lines[s + lineLengthIncrement]:
                            if re.search("length ", lines[s + lineLengthIncrement]) is not None:
                                les = lines[s + lineLengthIncrement].split()
                                if len(les) > 2:
                                    tsVal = les[1] + ' ' + les[2].strip(';')
                                    lengthVal = tsVal
                                elif len(les) <= 2:
                                    tsVal = les[1].strip(';')
                                    lengthVal = tsVal
                                break
                            else:
                                lineLengthIncrement = lineLengthIncrement + 1
                            if '}' in lines[s + lineLengthIncrement]:
                                lineLengthIncrement = 0
                                lengthVal = 'None'
                                break
                        if re.search("object underground_line", lines[s]) is not None:
                            lengthVal = "UG_line\\n" + lengthVal
                        elif re.search("object overhead_line", lines[s]) is not None:
                            lengthVal = "OH_line\\n" + lengthVal
                    elif re.search("object transformer", lines[s]) is not None:
                        edge_color = 'red'
                        lengthVal = "transformer\\n" + lengthVal
                        outfile.write("node [shape=oval]\n")
                    elif re.search("object triplex_line", lines[s]) is not None:
                        edge_color = 'green'
                        lengthVal = "triplex_line\\n" + lengthVal
                    elif re.search("object fuse", lines[s]) != None:
                        edge_color = 'blue'
                        lengthVal = "Fuse\\n" + lengthVal
                    elif re.search("phases ", lines[s]) != None:
                        ts = lines[s].split()
                        if len(ts[1].rstrip(';')) > 3:
                            edge_style = 'bold'
                        elif len(ts[1].rstrip(';')) > 2:
                            edge_style = 'dashed'

                s += 1

            outfile.write("}\n")
            infile.close()
            outfile.close()
            os.system("dot -Tsvg -O " + filename)
        
        else:
            print("[x] {}.{} is not a GridLAB-D File. Not trying to layout.".format(filename, file_extension))
            
    
    elif os.path.isdir(file_or_folder_name):
        print("[i] Trying to visualize all GLM files in: {}".format(file_or_folder_name))
        for f in os.listdir(file_or_folder_name):
            filename = os.path.join(file_or_folder_name, f)
            print("[i] Processing: {}".format(filename))
            layout_model(filename)
        
        
    
    else:
        print("[i] The parameter {} you used inside `layout_model({})` was not found to be either file or a directory.".format(file_or_folder_name, file_or_folder_name))
        print("[i] Please re-check the parameter. If error persists, check the Known Issues document.")
        return

    print("[i] Layout of all GridLAB-D files are complete.")
    print("[i] SVG files can be viewed in any web browser, and edited using Inkscape.")
    
    return

def realtime_demo():
    """
    """
    plt.axis([0,10,0,1])

    for i in range(10):
        y = np.random.random()
        plt.scatter(i,y)
        plt.pause(0.05)

    plt.show()

