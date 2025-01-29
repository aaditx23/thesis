import cv2
import os
from ultralytics import YOLO
from collections import defaultdict
from utils import draw_boxes

# Load the YOLO model
model = YOLO('zabir.pt')

class_list = model.names
print(class_list)

# Dictionary to store object counts by class
class_counts = defaultdict(int)
crossed_ids = set()

# Store frames in memory
video_frames = []
video_properties = {}
total = 0
current = 0

def process_frame(frame):
    """
    Annotates the given frame with detected objects and tracking info.
    Stores the processed frame in memory.
    """
    global video_frames

    # Run YOLO tracking on the frame
    results = model.track(frame, persist=True, classes=[1, 2, 3, 5, 6, 7])

    # Ensure results are not empty
    if results[0].boxes.data is not None:
        boxes = results[0].boxes.xyxy.cpu()
        track_ids = results[0].boxes.id
        if track_ids is not None:
            track_ids = track_ids.int().cpu().tolist()
        else:
            track_ids = [None] * len(boxes)  # Fill with None if no IDs are available
        class_indices = results[0].boxes.cls.int().cpu().tolist()
        confidences = results[0].boxes.conf.cpu()

        frame = draw_boxes(frame, boxes, class_list, class_indices, identities=track_ids)
    # Store the processed frame
    video_frames.append(frame)


def predict(source):
    """
    Reads frames from the video, processes them, and stores the annotated frames in memory.
    """
    global video_properties, total, current

    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    # Get video properties
    video_properties = {
        "frame_width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "frame_height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    }

    print(
        f"Total frames: {video_properties['total_frames']}, Resolution: {video_properties['frame_width']}x{video_properties['frame_height']}, FPS: {video_properties['fps']}")
    total = video_properties['total_frames']
    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        count += 1
        print(f"Processing frame: {count}/{video_properties['total_frames']}")
        current = count

        process_frame(frame)  # Process and store the frame



    cap.release()
    save_video()
    print("Video processing completed. Frames stored in memory.")


def save_video(output_path="runs/detect/output.mp4"):
    """
    Saves the stored frames as a video file.
    """
    global video_frames, video_properties

    if not video_frames:
        print("No frames to save!")
        return

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, video_properties["fps"],
                          (video_properties["frame_width"], video_properties["frame_height"]))

    for frame in video_frames:
        out.write(frame)

    out.release()
    print(f"Annotated video saved at: {output_path}")


# Run the pipeline
# predict("assets/short.mp4")
