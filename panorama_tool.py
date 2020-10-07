from cv2 import cv2
import numpy as np
import os
import math
from os import path
import sys
sys.path.insert(1, '/mnt/share/Local/OfflineDB/Scripts/tesviewer')
from Reader import *
from scipy.spatial import distance

ALL_FRAMES = True
NUM_BOOLS = 9
# Thermal:
IS_PANORAMA_ACTIVE = 26
BOOL_COL = 27
BOOL_ROW = 28
BOOL_LAT = 29
BOOL_LON = 30
BOOL_PITCH = 
BOOL_ROLL = 15
BOOL_YAW = 16

# VIS:
IS_PANORAMA_ACTIVE = 26
BOOL_COL = 27
BOOL_ROW = 28
BOOL_LAT = 29
BOOL_LON = 30


props_filename = input("Props file path: ")
movie_filename = input("Movie file path: ")

# constants
if movie_filename.endswith(".raw2"):
    width, height = (640, 480)
elif movie_filename.endswith(".rawc"):
    width, height = (720, 576)
else:
    width, height = (384, 288)
frame_size = height * width

reader = Reader(path1=movie_filename, width1=width, height1=height)
stable_frames_per_area = [None] * NUM_BOOLS

#globals
frames_data = []
is_stops_updated = False


class Frame_Data:
    def __init__(self):
        self.pitch = None
        self.roll = None
        self.yaw = None
        self.is_panorama = None
        self.area = None
        self.row = None
        self.col = None
        self.is_stable_frame = False


# clears screen
def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def table_from_txt_file(filename, delimiter=' '):
    result = [None] * NUM_BOOLS
    with open(filename, "r") as f:
        for i in range(NUM_BOOLS):
            line = f.readline()
            elements = line.split(delimiter)
            result[i].append([float(elements[1]), float(elements[2]), float(elements[3])])
    
    return result


# updates global list 'frames_data' with pitch, roll and area data for each frame
def update_frame_data_list():
    for i in range(reader.num_frames1):
        current_frame = Frame_Data()
        pitch, roll, yaw, row, col, is_panorama = get_props_data(i)
        current_frame.pitch = float(pitch)
        current_frame.roll = float(roll)
        current_frame.yaw = float(yaw)
        current_frame.is_panorama = int(is_panorama)
        current_frame.row = int(row)
        current_frame.col = int(col)
        current_frame.area = get_area_from_row_col(current_frame.row, current_frame.col)
        # current_frame.area = int(get_closest_area(current_frame.pitch, current_frame.roll, current_frame.yaw))
        frames_data.append(current_frame)


def get_area_from_row_col(row, col):
    if row == 0 and col == 0:
        area = 7
    elif row == 0 and col == 1:
        area = 8
    elif row == 0 and col == 2:
        area = 9
    elif row == 1 and col == 0:
        area = 6
    elif row == 1 and col == 1:
        area = 5
    elif row == 1 and col == 2:
        area = 4
    elif row == 2 and col == 0:
        area = 1
    elif row == 2 and col == 1:
        area = 2
    else:
        area = 3
    
    return area


# reads one frame from the file and displays it
# overlays a header with information if needed
def show_frame(filename, index, header, scale=(height, width)):
    frame = reader.get_frame(index=index, bgr=True)
    if header is not None:
        overlay_text_on_image(frame, header)

    # resizing the window for convenience:
    if scale == (1440, 1920):
        cv2.namedWindow('frames', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('frames', 1344, 1008)
    cv2.imshow('frames', frame)


# converts a uint8 format nparray into uint16 format
def uint8_to_uint16_image(image):
    min_value = np.amin(image)
    max_value = np.amax(image)
    original_range = max_value - min_value
    # to avoid dividing by 0
    if original_range == 0:
        original_range = 255

    scale = 65535.0/np.float(original_range)
    transform_image = (image - min_value).astype(np.float) * scale
    transform_image = np.around(transform_image)
    transform_image = np.uint16(transform_image)

    return transform_image


# returns a string header with the frame's information
def build_image_header(frame_number, show_area):
    header = 'frame #' + str(frame_number) + ' pitch: ' + str(frames_data[frame_number].pitch) + ' roll: ' + str(frames_data[frame_number].roll) + ' yaw: ' + str(frames_data[frame_number].yaw)

    if (show_area is True):
        area = str(frames_data[frame_number].area)
        header = header + ' area: ' + area

    return header


# returns header string in the divided video format
def build_image_header_for_divided_video(area, frame_number):
    text_file = open('area'+str(area)+'.txt', 'r')
    for i in range(frame_number):
        line = text_file.readline()
    split_line = line.split(' ')
    header = 'area: ' + str(area) + ' original frame number: ' + str(split_line[3])
    text_file.close()
    return header


# returns 'image' with the overlay header
def overlay_text_on_image(image, header, scale=0.5):
    font = cv2.FONT_HERSHEY_DUPLEX
    bottom_left_corner_of_text = (10, 20)
    font_scale = scale
    font_color = (255, 255, 255)
    line_type = 1

    cv2.putText(image, header,
                bottom_left_corner_of_text,
                font,
                font_scale,
                font_color,
                line_type)

    return image


# displays camera film from frame 'start'.
# 'show_header' and 'show_area' indicate if header/area display is needed
def display_movie(start, show_header, show_area):
    header = None
    for i in range(start, reader.num_frames1):
        if show_header is True:
            header = build_image_header(i, show_area)
        show_frame(movie_filename, i, header)
        cv2.waitKey(10)
    cv2.destroyAllWindows()


# returns pitch, roll and yaw for 'frame_number' frame
def get_props_data(frame_number):
    with open(props_filename, 'r') as f:
        for i in range(frame_number + 1):
            line = f.readline()
        split_line = line.split()
        pitch, roll, yaw = int(split_line[BOOL_PITCH])/100.0, int(split_line[BOOL_ROLL])/100.0, int(split_line[BOOL_YAW])/100.0
        row, col = split_line[BOOL_ROW], split_line[BOOL_COL]
        is_panorama = split_line[IS_PANORAMA_ACTIVE]
        return (pitch, roll, yaw, row, col, is_panorama)


# returns the most stable frame index between frame indexes 'start' and 'end'
def get_stable_frame_index_in_stop(start, end):
    min_movement = get_previous_next_distance(start)
    best_frame = start
    for i in range(start+1, end+1):
        current_movement = get_previous_next_distance(i)
        if current_movement < min_movement:
            frame = reader.get_frame(index=i, bgr=True)
            if is_blackened_image(frame) is False:
                min_movement = current_movement
                best_frame = i

    frames_data[best_frame].is_stable_frame = True
    return best_frame


# calculates and returns the distance (movement) between previous and next frame
# relatively to frame in index 'frame_number'
def get_previous_next_distance(frame_number):
    previous_point = (frames_data[frame_number - 1].pitch, frames_data[frame_number - 1].roll, frames_data[frame_number - 1].yaw)
    current_point = (frames_data[frame_number].pitch, frames_data[frame_number].roll, frames_data[frame_number].yaw)
    distance = compute_euclidean_distance(previous_point, current_point)
    if frame_number < reader.num_frames1 - 1:
        next_point = (frames_data[frame_number+1].pitch, frames_data[frame_number+1].roll, frames_data[frame_number + 1].yaw)
        distance += compute_euclidean_distance(current_point, next_point)

    return distance


# returns True if the frame is averagely black, False if not
def is_blackened_image(frame):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    average = np.mean(gray_frame)
    
    if average < 50:
        return True
    else:
        return False


# # returns the area number that is the closest, considering the given pitch and roll
# def get_closest_area(pitch, roll, yaw):
#     min_distance = compute_euclidean_distance((float(pitch), float(roll), float(yaw)), areas_coordinates[0])
#     closest_area = 1

#     for i in range(1, 9):
#         current_distance = compute_euclidean_distance((float(pitch), float(roll), float(yaw)), areas_coordinates[i])
#         if current_distance < min_distance:
#             closest_area = i+1
#             min_distance = current_distance

#     return closest_area


# calculates and returns the distance between p1 and p2
def compute_euclidean_distance(p1, p2):
    d = distance.euclidean(p1, p2)
    return d


# opens and updates .txt and .raw2 files with most stable frames for each area from frame 698
def create_divided_videos_by_area(all_frames=False):
    cls()
    print("The system finds the most stable frames")
    print("The process might take few seconds, please be patient...")
    # array of binary raw
    raw_file = [0] * NUM_BOOLS
    # array of text files
    text_file = [0] * NUM_BOOLS
    # array that stores c
    frame_counter = [0] * NUM_BOOLS

    # open files:
    for i in range(NUM_BOOLS):
        raw_file[i] = open('area' + str(i+1) + "." + movie_filename.split('.')[-1], 'wb')
        text_file[i] = open('area' + str(i+1) + '.txt', 'w')

    # update_frame_data_list()
    start = 0

    while start < reader.num_frames1:
        while frames_data[start].is_panorama == 0 and start < reader.num_frames1:
            start += 1
        end = start
        while frames_data[start].is_panorama == frames_data[end].is_panorama == 1 and end < reader.num_frames1-1 and frames_data[end].area == frames_data[start].area:
            end += 1
        if end > start:
            end -= 1

        frames_indexes = []
        if all_frames is False:
            frames_indexes.append(get_stable_frame_index_in_stop(start, end))
        else:
            for j in range(start, end+1):
                frames_indexes.append(j)
        
        for idx in frames_indexes:
            frame = reader.get_frame(index=idx, bgr=False)
            raw_file[frames_data[idx].area - 1].write(frame)
            text_file[frames_data[idx].area - 1].write('frame number ' + str(frame_counter[frames_data[idx].area - 1])+': '+str(idx) + ' \n')
            frame_counter[frames_data[idx].area - 1] += 1
        start = end + 1

    global is_stops_updated
    is_stops_updated = True
    # close files:
    for i in range(NUM_BOOLS):
        raw_file[i].close()
        text_file[i].close()


# displays all divided videos one by one
def display_divided_videos():
    # if path.exists('area1' + "." + movie_filename.split('.')[-1]) is False:
    create_divided_videos_by_area(ALL_FRAMES)
    for i in range(NUM_BOOLS):
        display_divided_video_by_area(i + 1)


# displays the divided video for the specified area
def display_divided_video_by_area(area):
    filename = 'area' + str(area) + '.txt'
    num_lines = file_len(filename)

    for i in range(num_lines):
        header = build_image_header_for_divided_video(area, i+1)
        show_frame('area' + str(area) + "." + movie_filename.split('.')[-1], i, header)
        cv2.waitKey(10)
    cv2.destroyAllWindows()


# returns num of lines in 'filename'
def file_len(filename):
    with open(filename) as f:
        for i, l in enumerate(f):
            pass
    return i


# creates the area map image and displays it
def create_and_show_area_map():
    area_map = create_area_map()
    show_area_map(area_map)

    return area_map


# creates the area map image
def create_area_map():
    # if path.exists("area1." + movie_filename.split('.')[-1]) is False:
    create_divided_videos_by_area(ALL_FRAMES)
    area_images = [None] * NUM_BOOLS

    for i in range(NUM_BOOLS):
        filename = 'area' + str(i+1) + '.' + movie_filename.split('.')[-1]
        area_reader = Reader(path1=filename, width1=width, height1=height)
        area_images[i] = area_reader.get_frame(index=0, bgr=True)

    panorama_width = width * 3
    panorama_height = height * 3

    base_image = np.zeros((panorama_height, panorama_width, 3), np.uint8)

    for i in range(NUM_BOOLS):
        position = (get_image_position_by_area(i+1))
        overlay_images_in_position(base_image, area_images[i], position)

    cv2.imwrite('map_area_file.png', base_image)
    # with open('area_map.txt', 'wb') as map_file:
    #     map_file.write(base_image)

    return base_image


# displays the area map image
def show_area_map(image):
    cv2.namedWindow('area map', cv2.WINDOW_NORMAL)
    cv2.imshow('area map', image)
    cv2.waitKey(0)  # waits until a key is pressed
    cv2.destroyAllWindows()  # destroys the window showing image


# overlays 'top_image' on top of 'base_image'
def overlay_images_in_position(base_image, top_image, position):
    base_image[position[1]:position[1] + top_image.shape[0], position[0]:position[0] + top_image.shape[1], :] = top_image
    return base_image


# returns the required position in the area map image according to the area
def get_image_position_by_area(area):
    position = [0] * 2

    if area in (1, 6, 7):
        position[0] = 0
    elif area in (2, 5, 8):
        position[0] = width
    else:
        position[0] = width * 2

    if area in (1, 2, 3):
        position[1] = height * 2
    elif area in(4, 5, 6):
        position[1] = height
    else:
        position[1] = 0

    return position


# displays the area map video
def show_area_map_video(show_header):
    # if is_stops_updated is False:
    create_divided_videos_by_area(ALL_FRAMES)

    cls()
    print("Writing frames into raw file")
    print("The process might take a minute, please be patient...")
    panorame_width = width * 3
    panorama_height = height * 3
    base_frame = np.zeros((panorama_height, panorame_width, 3), np.uint8)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    videowriter = cv2.VideoWriter('area_map.mp4', fourcc, 1, (panorame_width, panorama_height))

    for i in range(reader.num_frames1):
        if frames_data[i].is_stable_frame is True:
            top_frame = reader.get_frame(index=i, bgr=True)
            position = get_image_position_by_area(frames_data[i].area)
            base_frame = overlay_images_in_position(base_frame, top_frame, position)

            if show_header is not False:
                text_background = np.zeros((35, panorame_width, 3), np.uint8)
                base_frame = overlay_images_in_position(base_frame, text_background, (0, 0))
                header = 'Current Frame in Area: ' + str(frames_data[i].area) + '   -   Frame number: ' + str(i)
                overlay_text_on_image(base_frame, header, 1)

            videowriter.write(base_frame)

    videowriter.release()
    display_area_map_video_from_file('area_map.mp4')


# reads from .raw2 file 'raw_filename' the area map video and displays it
def display_area_map_video_from_file(filename):
    area_map_reader = Reader(path1=filename)
    area_map_reader.display()


# displays the user's menu
def display_menu():
    update_frame_data_list()

    menu = {}
    menu['1'] = "Display Entire Video"
    menu['2'] = "Display Video From Selected Frame"
    menu['3'] = "Display Video - Show Frame#, Pitch, Roll, Yaw and Area"
    menu['4'] = "Create RAW File and Text File For Each Area in Current Directory"
    menu['5'] = "Display Divided Videos By Area"
    menu['6'] = "Create Area Map"
    menu['7'] = "Display Area Map Video"
    menu['8'] = "Display Area Map Video - Show Area and Frame#"
    menu['9'] = "Exit"

    while True:
        cls()

        print('======== System Menu ========')
        options = menu.keys()
        for entry in options:
            print(entry, menu[entry])

        selection = input("Please Select: ")

        if selection == '1':
            display_movie(0, False, False)
        elif selection == '2':
            from_frame = int(input("Select frame number to start from: "))
            display_movie(from_frame, False, False)
        elif selection == '3':
            display_movie(0, True, True)
        elif selection == '4':
            create_divided_videos_by_area(ALL_FRAMES)
        elif selection == '5':
            display_divided_videos()
        elif selection == '6':
            create_and_show_area_map()
        elif selection == '7':
            show_area_map_video(False)
        elif selection == '8':
            show_area_map_video(True)
        elif selection == '9':
            exit(1)
        else:
            print("Unknown Option Selected!")


display_menu()

