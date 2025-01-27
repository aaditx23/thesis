from PyQt5 import QtWidgets
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl
import sys
import hydra
import os

from pathlib import Path

from ultralytics.yolo.utils import DEFAULT_CONFIG
from ultralytics.yolo.utils.checks import check_imgsz

from DetectionPredictor import DetectionPredictor

from pythonProject.LaneAdjustment import LaneAdjustmentApp
import cv2

source = 0
output = ""
fileName = ""

# Use Hydra to manage the configuration
def clear_data():
    file = open("data.txt", 'w')
    file.close()
@hydra.main(version_base=None, config_path=str(DEFAULT_CONFIG.parent), config_name=DEFAULT_CONFIG.name)
def predict_webcam(cfg):
    global output
    clear_data()
    if source != 0:
        print(cfg)
        cfg.model = cfg.model or "yolov8n.pt"
        cfg.imgsz = check_imgsz(cfg.imgsz, min_dim=2)  # check image size
        cfg.source = source
        predictor = DetectionPredictor(cfg)
        predictor()
        output = predictor.save_dir
        print("PATH HAHAHA", output)
class VideoProcessingApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.video = "No video Selected"

        self.setWindowTitle("Vehicle Metrics Processor")
        self.setGeometry(100, 100, 800, 600)

        # Layouts
        self.layout = QtWidgets.QVBoxLayout()
        self.controls_layout = QtWidgets.QHBoxLayout()
        self.video_layout = QtWidgets.QVBoxLayout()

        # Controls
        self.upload_button = QtWidgets.QPushButton("Browse for Video")
        self.upload_button.clicked.connect(self.browse_video)

        # Display the selected video path
        self.video_path_label = QtWidgets.QLabel(self.video)

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
            if "runs/detect/train" in str(output):
                relativePath = str(output) + "/" + fileName
                video = str(Path(relativePath).absolute())
                print("VIDEO IS ", video)
                self.player = QMediaPlayer()
                media_content = QMediaContent(QUrl.fromLocalFile(video))
                self.player.setMedia(media_content)
                self.player.setVideoOutput(self.video_widget)
                self.player.play()
            else:
                print("loading screen")
        else:
            QtWidgets.QMessageBox.warning(self, "No Video Selected", "Please select a video to play.")

    # def browse_video(self):
    #     global fileName, source
    #     video_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Video File", "", "MP4 Files (*.mp4)")
    #     if video_file:
    #         self.video_path = video_file
    #         self.video_path_label.setText(f"Video Path: {self.video_path}")
    #
    #         fileName = os.path.basename(self.video_path)
    #         source = self.video_path
    #         self.video = source
    #         print(fileName)
    #         self.play_video()

    def browse_video(self):
        global fileName, source
        video_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Video File", "", "MP4 Files (*.mp4)")
        if video_file:
            self.video_path = video_file
            self.video_path_label.setText(f"Video Path: {self.video_path}")

            fileName = os.path.basename(self.video_path)
            source = self.video_path
            self.video = source

            # Capture the first frame
            cap = cv2.VideoCapture(video_file)

            # Check if the video was opened successfully
            if not cap.isOpened():
                print("Error: Could not open video.")
                return

            # Set the video capture to the 10th frame
            frame_number = 10
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

            # Read the 10th frame
            ret, frame = cap.read()
            cap.release()

            if ret:
                self.frame = frame

                # Open the lane adjustment window
                self.lane_adjustment_window = LaneAdjustmentApp(frame=self.frame)
                self.lane_adjustment_window.show()




if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = VideoProcessingApp()
    window.show()
    sys.exit(app.exec_())