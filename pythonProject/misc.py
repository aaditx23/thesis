# def draw_boxes(img, bbox, names, object_id, identities=None, offset=(0, 0)):
#     cv2.line(img, line[0], line[1], (46, 162, 112), 3)
#
#     print(f"Identities: {identities}")
#     print(f"Data Deque Keys: {list(data_deque.keys())}")
#
#     height, width, _ = img.shape
#     # remove tracked point from buffer if object is lost
#     for key in list(data_deque):
#         if key not in identities:
#             data_deque.pop(key)
#
#     for i, box in enumerate(bbox):
#         x1, y1, x2, y2 = [int(i) for i in box]
#         x1 += offset[0]
#         x2 += offset[0]
#         y1 += offset[1]
#         y2 += offset[1]
#
#         # code to find center of bottom edge
#         center = (int((x2 + x1) / 2), int((y2 + y2) / 2))
#
#         # get ID of object
#         id = int(identities[i]) if identities is not None else 0
#         # Ensure the id exists in data_deque before using it
#
#         # create new buffer for new object
#         if id not in data_deque:
#             data_deque[id] = deque(maxlen=64)
#             speed_line_queue[id] = []
#         color = compute_color_for_labels(object_id[i])
#         obj_name = names[object_id[i]]
#         label = '{}{:d}'.format("", id) + ":" + '%s' % (obj_name)
#
#         # add center to buffer
#         data_deque[id].appendleft(center)
#         if len(data_deque[id]) >= 2:
#             direction = get_direction(data_deque[id][0], data_deque[id][1])
#             object_speed = estimatespeed(data_deque[id][1], data_deque[id][0])
#             speed_line_queue[id].append(object_speed)
#             if intersect(data_deque[id][0], data_deque[id][1], line[0], line[1]):
#                 cv2.line(img, line[0], line[1], (255, 255, 255), 3)
#                 if "South" in direction:
#                     if obj_name not in object_counter:
#                         object_counter[obj_name] = 1
#                     else:
#                         object_counter[obj_name] += 1
#                 if "North" in direction:
#                     if obj_name not in object_counter1:
#                         object_counter1[obj_name] = 1
#                     else:
#                         object_counter1[obj_name] += 1
#
#         try:
#             label = label + " " + str(sum(speed_line_queue[id]) // len(speed_line_queue[id])) + "km/h"
#         except:
#             pass
#         UI_box(box, img, label=label, color=color, line_thickness=2)
#         # draw trail
#         for i in range(1, len(data_deque[id])):
#             # check if on buffer value is none
#             if data_deque[id][i - 1] is None or data_deque[id][i] is None:
#                 continue
#             # generate dynamic thickness of trails
#             thickness = int(np.sqrt(64 / float(i + i)) * 1.5)
#             # draw trails
#             cv2.line(img, data_deque[id][i - 1], data_deque[id][i], color, thickness)
#
#         # 4. Display Count in top right corner
#         for idx, (key, value) in enumerate(object_counter1.items()):
#             cnt_str = str(key) + ":" + str(value)
#             cv2.line(img, (width - 500, 25), (width, 25), [85, 45, 255], 40)
#             cv2.putText(img, f'Number of Vehicles Entering', (width - 500, 35), 0, 1, [225, 255, 255], thickness=2,
#                         lineType=cv2.LINE_AA)
#             cv2.line(img, (width - 150, 65 + (idx * 40)), (width, 65 + (idx * 40)), [85, 45, 255], 30)
#             cv2.putText(img, cnt_str, (width - 150, 75 + (idx * 40)), 0, 1, [255, 255, 255], thickness=2,
#                         lineType=cv2.LINE_AA)
#
#         for idx, (key, value) in enumerate(object_counter.items()):
#             cnt_str1 = str(key) + ":" + str(value)
#             cv2.line(img, (20, 25), (500, 25), [85, 45, 255], 40)
#             cv2.putText(img, f'Numbers of Vehicles Leaving', (11, 35), 0, 1, [225, 255, 255], thickness=2,
#                         lineType=cv2.LINE_AA)
#             cv2.line(img, (20, 65 + (idx * 40)), (127, 65 + (idx * 40)), [85, 45, 255], 30)
#             cv2.putText(img, cnt_str1, (11, 75 + (idx * 40)), 0, 1, [225, 255, 255], thickness=2, lineType=cv2.LINE_AA)
#         write_to_file(bbox, identities, obj_name, offset)
#     return img