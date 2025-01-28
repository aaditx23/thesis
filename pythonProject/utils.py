# Ultralytics YOLO 🚀, GPL-3.0 license

import math
from collections import deque
import cv2
import numpy as np
from numpy import random
from deep_sort_pytorch.deep_sort import DeepSort
from deep_sort_pytorch.utils.parser import get_config
from dataclasses import dataclass


@dataclass
class Vehicle:
    id: int
    velocity: str
    direction: str
    name: str
    lane: int = 0


palette = (2 ** 11 - 1, 2 ** 15 - 1, 2 ** 20 - 1)
data_deque = {}
object_counter = {}
object_counter1 = {}
speed_line_queue = {}

vehicle_in = {}
vehicle_out = {}
lanes = []


def estimatespeed(Location1, Location2):
    # Euclidean Distance Formula
    d_pixel = math.sqrt(math.pow(Location2[0] - Location1[0], 2) + math.pow(Location2[1] - Location1[1], 2))
    # defining thr pixels per meter
    ppm = 8
    d_meters = d_pixel / ppm
    time_constant = 15 * 3.6
    # distance = speed/time
    speed = d_meters * time_constant

    return int(speed)


def init_tracker():
    cfg_deep = get_config()
    cfg_deep.merge_from_file("deep_sort_pytorch/configs/deep_sort.yaml")

    deepsort = DeepSort(cfg_deep.DEEPSORT.REID_CKPT,
                        max_dist=cfg_deep.DEEPSORT.MAX_DIST, min_confidence=cfg_deep.DEEPSORT.MIN_CONFIDENCE,
                        nms_max_overlap=cfg_deep.DEEPSORT.NMS_MAX_OVERLAP,
                        max_iou_distance=cfg_deep.DEEPSORT.MAX_IOU_DISTANCE,
                        max_age=cfg_deep.DEEPSORT.MAX_AGE, n_init=cfg_deep.DEEPSORT.N_INIT,
                        nn_budget=cfg_deep.DEEPSORT.NN_BUDGET,
                        use_cuda=True)

    return deepsort


##########################################################################################
def xyxy_to_xywh(*xyxy):
    """" Calculates the relative bounding box from absolute pixel values. """
    bbox_left = min([xyxy[0].item(), xyxy[2].item()])
    bbox_top = min([xyxy[1].item(), xyxy[3].item()])
    bbox_w = abs(xyxy[0].item() - xyxy[2].item())
    bbox_h = abs(xyxy[1].item() - xyxy[3].item())
    x_c = (bbox_left + bbox_w / 2)
    y_c = (bbox_top + bbox_h / 2)
    w = bbox_w
    h = bbox_h
    return x_c, y_c, w, h


def xyxy_to_tlwh(bbox_xyxy):
    tlwh_bboxs = []
    for i, box in enumerate(bbox_xyxy):
        x1, y1, x2, y2 = [int(i) for i in box]
        top = x1
        left = y1
        w = int(x2 - x1)
        h = int(y2 - y1)
        tlwh_obj = [top, left, w, h]
        tlwh_bboxs.append(tlwh_obj)
    return tlwh_bboxs


def compute_color_for_labels(label):
    """
    Simple function that adds fixed color depending on the class
    """
    if label == 0:  # person
        color = (85, 45, 255)
    elif label == 2:  # Car
        color = (222, 82, 175)
    elif label == 3:  # Motorbike
        color = (0, 204, 255)
    elif label == 5:  # Bus
        color = (0, 149, 255)
    else:
        color = [int((p * (label ** 2 - label + 1)) % 255) for p in palette]
    return tuple(color)


def draw_border(img, pt1, pt2, color, thickness, r, d):
    x1, y1 = pt1
    x2, y2 = pt2
    # Top left
    cv2.line(img, (x1 + r, y1), (x1 + r + d, y1), color, thickness)
    cv2.line(img, (x1, y1 + r), (x1, y1 + r + d), color, thickness)
    cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)
    # Top right
    cv2.line(img, (x2 - r, y1), (x2 - r - d, y1), color, thickness)
    cv2.line(img, (x2, y1 + r), (x2, y1 + r + d), color, thickness)
    cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)
    # Bottom left
    cv2.line(img, (x1 + r, y2), (x1 + r + d, y2), color, thickness)
    cv2.line(img, (x1, y2 - r), (x1, y2 - r - d), color, thickness)
    cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness)
    # Bottom right
    cv2.line(img, (x2 - r, y2), (x2 - r - d, y2), color, thickness)
    cv2.line(img, (x2, y2 - r), (x2, y2 - r - d), color, thickness)
    cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness)

    cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, -1, cv2.LINE_AA)
    cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r - d), color, -1, cv2.LINE_AA)

    cv2.circle(img, (x1 + r, y1 + r), 2, color, 12)
    cv2.circle(img, (x2 - r, y1 + r), 2, color, 12)
    cv2.circle(img, (x1 + r, y2 - r), 2, color, 12)
    cv2.circle(img, (x2 - r, y2 - r), 2, color, 12)

    return img


def UI_box(x, img, color=None, label=None, line_thickness=None):
    # Plots one bounding box on image img
    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1  # line/font thickness
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]

        img = draw_border(img, (c1[0], c1[1] - t_size[1] - 3), (c1[0] + t_size[0], c1[1] + 3), color, 1, 8, 2)

        cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)


# def intersect(A, B, C, D):
#     return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)
#
#
# def ccw(A, B, C):
#     return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

def intersect(A, B, C, D):
    """
    Check if a bounding box (A, B) intersects with a horizontal lane (C, D).

    :param A, B: Bounding box coordinates (x1, y1) and (x2, y2) for the vehicle.
    :param C, D: Lane coordinates (x1, y1) and (x2, y2) for the lane (must be horizontal).
    :return: True if the bounding box intersects with the lane, False otherwise.
    """
    # Ensure the lane is horizontal by checking if the y-coordinates are the same
    if C[1] != D[1]:
        raise ValueError("Lane must be a horizontal line.")

    # Check if the bounding box overlaps with the lane vertically (Y-range overlap)
    if min(A[1], B[1]) <= C[1] <= max(A[1], B[1]):
        # Check if the bounding box horizontally overlaps with the lane
        if (C[0] <= A[0] <= D[0]) or (C[0] <= B[0] <= D[0]) or (A[0] <= C[0] <= B[0]):
            return True

    return False


def get_direction(point1, point2):
    direction_str = ""

    # calculate y axis direction
    if point1[1] > point2[1]:
        direction_str += "South"
    elif point1[1] < point2[1]:
        direction_str += "North"
    else:
        direction_str += ""

    # calculate x axis direction
    if point1[0] > point2[0]:
        direction_str += "East"
    elif point1[0] < point2[0]:
        direction_str += "West"
    else:
        direction_str += ""

    return direction_str


def add_vehicle_in(vehicle: Vehicle):
    if vehicle.name not in vehicle_in:
        vehicle_in[vehicle.name] = [vehicle]
    else:
        vehicle_in[vehicle.name].append(vehicle)


def add_vehicle_out(vehicle: Vehicle):
    if vehicle.name not in vehicle_out:
        vehicle_out[vehicle.name] = [vehicle]
    else:
        vehicle_out[vehicle.name].append(vehicle)


def add_vehicle(id, velocity, direction, obj_name, lane):
    vehicle = Vehicle(
        id=id,
        velocity=f"{velocity} km/h",
        name=obj_name,
        direction="",
        lane=lane
    )
    # Determine direction ("in" or "out")
    if "South" in direction:
        vehicle.direction = "in"
        add_vehicle_in(vehicle)
    elif "North" in direction:
        vehicle.direction = "out"
        add_vehicle_out(vehicle)

    write_to_file(vehicle)


def draw_trail(id, img, color):
    for i in range(1, len(data_deque[id])):
        # Check if on buffer value is none
        if data_deque[id][i - 1] is None or data_deque[id][i] is None:
            continue
        # Generate dynamic thickness of trails
        thickness = int(np.sqrt(64 / float(i + i)) * 1.5)
        # Draw trails
        cv2.line(img, data_deque[id][i - 1], data_deque[id][i], color, thickness)


def show_in(img, width):
    """
    Displays the number of vehicles leaving ("out") based on object_data dictionary.
    """
    for idx, (label, vehicles) in enumerate(vehicle_in.items()):
        if vehicles is not None:
            count = len(list(vehicles))
            cnt_str = f"{label}: {count}"
            cv2.line(img, (width - 500, 25), (width, 25), [85, 45, 255], 40)
            cv2.putText(img, 'Number of Vehicles Entering', (width - 500, 35), 0, 1, [225, 255, 255], thickness=2,
                        lineType=cv2.LINE_AA)
            cv2.line(img, (width - 150, 65 + (idx * 40)), (width, 65 + (idx * 40)), [85, 45, 255], 30)
            cv2.putText(img, cnt_str, (width - 150, 75 + (idx * 40)), 0, 1, [255, 255, 255], thickness=2,
                        lineType=cv2.LINE_AA)


def show_out(img):
    """
    Displays the number of vehicles entering ("in") based on object_data dictionary.
    """
    for idx, (label, vehicles) in enumerate(vehicle_out.items()):
        if vehicles is not None:
            count = len(list(vehicles))
            cnt_str1 = f"{label}: {count}"
            cv2.line(img, (20, 25), (500, 25), [85, 45, 255], 40)
            cv2.putText(img, 'Number of Vehicles Leaving', (11, 35), 0, 1, [225, 255, 255], thickness=2,
                        lineType=cv2.LINE_AA)
            cv2.line(img, (20, 65 + (idx * 40)), (127, 65 + (idx * 40)), [85, 45, 255], 30)
            cv2.putText(img, cnt_str1, (11, 75 + (idx * 40)), 0, 1, [225, 255, 255], thickness=2, lineType=cv2.LINE_AA)


def draw_boxes(img, bbox, names, object_id, identities=None, offset=(0, 0)):
    frame_height = img.shape[0]
    line_y = frame_height - (frame_height // 3)
    lane_lines = lanes[:len(lanes) - 1]
    crossing = lanes[-1]

    # crossing.draw(img)
    for lane in lane_lines:
        lane.draw(img)



    height, width, _ = img.shape
    # Remove tracked point from buffer if object is lost
    for key in list(data_deque):
        if key not in identities:
            data_deque.pop(key)

    for i, box in enumerate(bbox):
        x1, y1, x2, y2 = [int(i) for i in box]
        x1 += offset[0]
        x2 += offset[0]
        y1 += offset[1]
        y2 += offset[1]

        # Code to find center of bottom edge
        center = (int((x2 + x1) / 2), int((y2 + y2) / 2))

        # Get ID of object
        id = int(identities[i]) if identities is not None else 0

        # Create new buffer for new object
        if id not in data_deque:
            data_deque[id] = deque(maxlen=64)
        color = compute_color_for_labels(object_id[i])
        obj_name = names[object_id[i]]  # Object label (e.g., "Car", "Bus")
        label = '{}{:d}'.format("", id) + ":" + '%s' % (obj_name)

        # Add center to buffer
        data_deque[id].appendleft(center)
        if len(data_deque[id]) >= 2:
            direction = get_direction(data_deque[id][0], data_deque[id][1])

            if intersect(data_deque[id][0], data_deque[id][1], crossing.start(), crossing.end()):
                # Determine which lane segment was crossed
                lane_number = 0
                for idx, lane in enumerate(lane_lines):
                    if id == 13 or id == 18 or id == 20:
                        print(id, "DATA DEQUE ", data_deque[id][0], data_deque[id][1], lane.start(), lane.end(), intersect(data_deque[id][0], data_deque[id][1], lane.start(), lane.end() ))
                    if intersect(data_deque[id][0], data_deque[id][1], lane.start(), lane.end() ):
                        lane.blink(img)
                        lane_number = idx + 1  # Lane numbers start at 1
                        break

                # Calculate velocity
                velocity = estimatespeed(data_deque[id][1], data_deque[id][0])
                if lane_number != 0:
                    add_vehicle(id, velocity, direction, obj_name, lane_number)

        UI_box(box, img, label=label, color=color, line_thickness=2)
        draw_trail(id, img, color)

    show_in(img, width)
    show_out(img)

    return img


def write_to_file(vehicle: Vehicle):
    with open('data.txt', 'a') as file:  # Open file in append mode
        file.write(
            f"Object ID: {vehicle.id}, Velocity: {vehicle.velocity}, Direction: {vehicle.direction}, Lane: {vehicle.lane}, Label: {vehicle.name}\n")
