from cv2 import cv2
import numpy as np
import os
import sys
sys.path.insert(1, '/mnt/share/Local/OfflineDB/Scripts/tesviewer')
from Reader import *

dir_path = input("Please enter directory path: ")
extension = input("Please enter movie extension: ")
width = int(input("Movie width: "))
height = int(input("Movie height: "))
with_props = input("Create a full props file? Please enter y/n: ")

if with_props is 'y' or 'Y':
    with_props = True
else:
    with_props = False

movie_basename = os.path.basename(dir_path) + extension
movie_path = os.path.join(dir_path, movie_basename)
full_movie = open(movie_path, "wb")
if with_props is True:
    props_basename = movie_basename.replace(extension, '.props')
    props_path = os.path.join(dir_path, props_basename)
    full_props = open(props_path, "w")

for file in os.listdir(dir_path):
    if file.endswith(extension) and file not in movie_basename:
        print("Adding " + file)
        current_movie = os.path.join(dir_path, file)
        reader = Reader(path1=current_movie, width1=width, height1=height)
        for i in range(reader.num_frames1):
            frame = reader.get_frame(index=i)
            full_movie.write(frame)
            print(i)
        if with_props is True:
            current_props = current_movie.replace(extension, '.props')
            current_props = current_props.replace('r2', 'r0')
            current_props = current_props.replace('r1', 'r0')
            with open(current_props, "r") as f:
                props_lines = f.readlines()
            full_props.writelines(props_lines)

full_movie.close()
try:
    full_props.close()
except:
    pass