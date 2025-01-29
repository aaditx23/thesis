import cv2
import os
from collections import defaultdict
from PyQt5.QtCore import pyqtSignal, QObject, QThread
from ultralytics import YOLO
from utils import draw_boxes


class Predictor(QThread):
    """
    A class for processing videos using YOLO for object detection and tracking.
    Stores processed frames in memory and allows saving the annotated video.
    """
    update_frame = pyqtSignal()
    completed = pyqtSignal()
    def __init__(self, model_path='zabir.pt'):
        """
        Initializes the YOLO model and sets up storage for processed frames.
        """
        super().__init__()
        self.model = YOLO(model_path)
        self.class_list = self.model.names
        self.class_counts = defaultdict(int)
        self.crossed_ids = set()

        self.video_frames = []  # Stores annotated frames
        self.video_properties = {}  # Stores video properties (width, height, FPS, total frames)
        self.total_frames = 0
        self.current_frame = 0
        self.source = 0

    def run(self):
        if self.source != 0:
            self.predict()
        else:
            print("Source not defined")

    def process_frame(self, frame):
        """
        Annotates a single frame using YOLO tracking and stores it.
        """
        # Run YOLO tracking
        results = self.model.track(frame, persist=True, classes=[1, 2, 3, 5, 6, 7])

        # Ensure results are not empty
        if results[0].boxes.data is not None:
            boxes = results[0].boxes.xyxy.cpu()
            track_ids = results[0].boxes.id
            track_ids = track_ids.int().cpu().tolist() if track_ids is not None else [None] * len(boxes)
            class_indices = results[0].boxes.cls.int().cpu().tolist()

            # Draw bounding boxes and tracking info
            frame = draw_boxes(frame, boxes, self.class_list, class_indices, identities=track_ids)

        # Store the processed frame
        self.video_frames.append(frame)

    def predict(self):
        """
        Reads frames from a video file, processes them, and stores annotated frames in memory.
        """
        cap = cv2.VideoCapture(self.source)

        if not cap.isOpened():
            print("Error: Could not open video.")
            return

        # Store video properties
        self.video_properties = {
            "frame_width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "frame_height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        }
        self.total_frames = self.video_properties["total_frames"]

        print(
            f"Total frames: {self.total_frames}, Resolution: {self.video_properties['frame_width']}x{self.video_properties['frame_height']}, FPS: {self.video_properties['fps']}")

        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            self.current_frame = frame_count  # Update current frame count
            self.update_frame.emit()
            print(f"Processing frame: {frame_count}/{self.total_frames}")

            self.process_frame(frame)  # Process and store the frame

        cap.release()
        self.save_video()
        print("Video processing completed. Frames stored in memory.")

    def save_video(self, output_path="runs/detect/output.mp4"):
        """
        Saves the processed frames as a video file.
        """
        if not self.video_frames:
            print("No frames to save!")
            return

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.video_properties["fps"],
                              (self.video_properties["frame_width"], self.video_properties["frame_height"]))

        for frame in self.video_frames:
            out.write(frame)

        out.release()
        print(f"Annotated video saved at: {output_path}")
        self.completed.emit()
