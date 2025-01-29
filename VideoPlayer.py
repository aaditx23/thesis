# VideoPlayer.py
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QMessageBox
from PyQt5.QtCore import QTimer


class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize video player components
        self.player = QMediaPlayer()
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")

        # Layouts for buttons and video
        self.layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()
        self.seekbar_layout = QHBoxLayout()

        # Create the play, pause, replay buttons
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Stop")
        self.replay_button = QPushButton("Replay")

        self.play_button.clicked.connect(self.play_video)
        self.pause_button.clicked.connect(self.pause_video)
        self.replay_button.clicked.connect(self.replay_video)

        # Add buttons to the horizontal layout
        self.button_layout.addWidget(self.play_button)
        self.button_layout.addWidget(self.pause_button)
        self.button_layout.addWidget(self.replay_button)

        # Create seekbar (QSlider)
        self.seekbar = QSlider(Qt.Horizontal)
        self.seekbar.setRange(0, 100)
        self.seekbar.setEnabled(False)

        # Add video widget, buttons, and seekbar to the layout
        self.layout.addWidget(self.video_widget)
        self.layout.addLayout(self.button_layout)
        self.layout.addWidget(self.seekbar)

        self.setLayout(self.layout)

        # Timer for updating the seekbar
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_seekbar)

        # Initialize video source
        self.source = None

    def play_video(self, source=None):
        """Play the video, or start playing if source is passed."""
        try:
            if source:
                self.source = source

            if not self.source:
                return

            # Set up video source
            media_content = QMediaContent(QUrl.fromLocalFile(self.source))
            self.player.setMedia(media_content)
            self.player.setVideoOutput(self.video_widget)

            # Play the video
            self.player.play()

            # Enable seekbar and start the timer for updating it
            self.seekbar.setEnabled(True)
            self.timer.start(100)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to play video: {str(e)}")

    def pause_video(self):
        """Pause the video."""
        self.player.pause()

    def replay_video(self):
        """Replay the video from the beginning."""
        self.player.setPosition(0)
        self.player.play()

    def update_seekbar(self):
        """Update the seekbar position based on the video time."""
        position = self.player.position()
        duration = self.player.duration()

        if duration > 0:
            # Update the seekbar's value
            self.seekbar.setValue(int((position / duration) * 100))

    def set_position(self, position):
        """Seek to a specific position in the video."""
        duration = self.player.duration()
        self.player.setPosition((position / 100) * duration)

    def disable_buttons(self):
        self.play_button.setDisabled(True)
        self.pause_button.setDisabled(True)
        self.replay_button.setDisabled(True)
        self.seekbar.setDisabled(True)
    def enable_buttons(self):
        self.play_button.setDisabled(False)
        self.pause_button.setDisabled(False)
        self.replay_button.setDisabled(False)
        self.seekbar.setDisabled(False)
