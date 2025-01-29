from PyQt5 import QtWidgets
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl
import sys
import os
from pathlib import Path
from LaneAdjustment import LaneAdjustmentApp
import cv2
import utils
import predict

source = 0
output = "runs/detect"
fileName = ""

# Use Hydra to manage the configuration
def clear_data():
    file = open("data.txt", 'w')
    file.close()
def predict_webcam():
    clear_data()
    if source != 0:
        predict.predict(source)
    print("Predicting")
class VideoProcessingApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.lanes_list = None
        self.frame = None
        self.lane_adjustment_window = None
        self.video = "No video Selected"
        self.lane_list = []
        self.setWindowTitle("Vehicle Metrics Processor")
        self.showNormal()

        # Layouts
        self.layout = QtWidgets.QVBoxLayout()
        self.controls_layout = QtWidgets.QHBoxLayout()
        self.video_layout = QtWidgets.QVBoxLayout()

        # Controls
        self.upload_button = QtWidgets.QPushButton("Browse for Video")
        self.upload_button.clicked.connect(self.browse_video)
        # adjust lane button
        self.lane_button = QtWidgets.QPushButton("Adjust Lanes")
        self.lane_button.clicked.connect(self.adjust_lane)
        # start processin button
        self.start_processing = QtWidgets.QPushButton("Start")
        self.start_processing.clicked.connect(self.start_prediction)

        # Display the selected video path
        self.video_path_label = QtWidgets.QLabel(self.video)

        #progress
        self.frame_progress_label = QtWidgets.QLabel("")
        self.frame_progress_label.setVisible(False)

        self.controls_layout.addWidget(self.upload_button)
        self.controls_layout.addWidget(self.video_path_label)

        # Video Display
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")

        self.video_layout.addWidget(self.video_widget)

        # Combine Layouts
        self.layout.addLayout(self.controls_layout)
        self.layout.addLayout(self.video_layout)
        self.setLayout(self.layout)

        # Video Player
        self.player = None
        self.video_path = None


    def play_video(self):
        if self.video_path:
            predict_webcam()

            relativePath = "runs/detect/output.mp4"
            video = str(Path(relativePath).absolute())
            print("VIDEO IS ", video)
            self.player = QMediaPlayer()
            media_content = QMediaContent(QUrl.fromLocalFile(video))
            self.player.setMedia(media_content)
            self.player.setVideoOutput(self.video_widget)
            self.player.play()

        else:
            QtWidgets.QMessageBox.warning(self, "No Video Selected", "Please select a video to play.")

    def update_frame_progress(self):
        """Update the frame progress label dynamically."""
        if hasattr(predict, "current") and hasattr(predict, "total"):
            self.frame_progress_label.setText(f"Frame: {predict.current}/{predict.total}")
    def browse_video(self):
        global fileName, source
        video_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Video File", "", "MP4 Files (*.mp4)")
        if video_file:
            self.video_path = video_file
            self.video_path_label.setText(f"Video Path: {self.video_path}")

            fileName = os.path.basename(self.video_path)
            source = self.video_path
            self.video = source
            self.controls_layout.addWidget(self.lane_button)



    def adjust_lane(self):
        # Capture the first frame
        cap = cv2.VideoCapture(self.video_path)

        # Check if the video was opened successfully
        if not cap.isOpened():
            print("Error: Could not open video.")
            return

        # Read the first frame
        ret, frame = cap.read()
        cap.release()

        if ret:
            self.frame = frame

            # Open the lane adjustment window and pass the first frame
            self.lane_adjustment_window = LaneAdjustmentApp(frame=self.frame)
            self.lane_adjustment_window.lanes_passed.connect(self.update_enabled_lanes)
            # self.lane_adjustment_window.window_closed.connect(self.play_video)
            self.lane_adjustment_window.show()
        else:
            print("Error: Could not read the first frame.")

    def update_enabled_lanes(self, lanes_list):
        utils.lanes = lanes_list
        self.controls_layout.addWidget(self.start_processing)
    def start_prediction(self):
        if hasattr(self, "start_processing"):
            self.controls_layout.removeWidget(self.start_processing)
            self.start_processing.deleteLater()
            del self.start_processing

            # Start the video processing
        self.play_video()

    def closeEvent(self, event):
        """Restore stdout and stderr when the app is closed."""
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        super().closeEvent(event)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = VideoProcessingApp()
    window.show()
    sys.exit(app.exec_())