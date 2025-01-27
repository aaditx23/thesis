from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from dataclasses import dataclass
import cv2
import random


@dataclass
class Lane:
    start_x: int
    width: int
    color: tuple
    enabled: bool = False
    y: int = 0
    thickness: int = 5

    @staticmethod
    def generate_color():
        """Generate a random bright color."""
        # Random bright colors are typically in the higher range of RGB values
        r = random.randint(128, 255)
        g = random.randint(128, 255)
        b = random.randint(128, 255)
        return (r, g, b)



class LaneAdjustmentApp(QtWidgets.QWidget):
    lanes_passed = pyqtSignal(list)  # Define the signal
    def __init__(self, frame, parent=None):
        super().__init__(parent)
        self.frame = frame
        self.frame_height = frame.shape[0]

        # Initialize lanes
        self.lanes = [
            Lane(
                start_x=100 + (i * 60),
                width=50,
                enabled=(i == 0),
                y=self.frame_height - (self.frame_height // 3),
                color=Lane.generate_color()
            )
            for i in range(8)
        ]

        # UI components for lane controls
        self.lane_controls = []

        self.setup_ui()
        self.render_frame_with_lanes()

    def setup_ui(self):
        """Set up the main UI components."""
        self.setWindowTitle("Lane Adjustment")
        self.setGeometry(200, 200, 1000, 800)
        self.layout = QtWidgets.QVBoxLayout()

        # Frame Display
        self.frame_label = QtWidgets.QLabel()
        self.frame_label.setStyleSheet("background-color: black;")
        self.frame_label.setFixedSize(800, 600)
        self.layout.addWidget(self.frame_label)

        # Lane Controls Layout
        self.controls_layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.controls_layout)

        # Lane Count Label
        self.lane_count_label = QtWidgets.QLabel("Enabled Lanes: 1")
        self.layout.addWidget(self.lane_count_label)

        # Create controls for all lanes
        self.create_lane_controls()

        # Buttons for finalizing or canceling
        self.add_bottom_buttons()

        self.setLayout(self.layout)

    def create_lane_controls(self):
        """Create controls for all lanes and add them to the UI."""
        for index, lane in enumerate(self.lanes):
            lane_layout = QtWidgets.QHBoxLayout()

            # Checkbox to enable/disable the lane
            checkbox = QtWidgets.QCheckBox(f"Lane {index + 1}")
            checkbox.setChecked(lane.enabled)
            checkbox.stateChanged.connect(
                lambda state, l=lane, idx=index: self.toggle_lane(state, l, idx)
            )
            lane_layout.addWidget(checkbox)

            # Create buttons using create_lane_button
            # Create buttons using create_lane_button
            left_button = self.create_lane_button("←", lane, lambda idx=index: self.adjust_lane(idx, -5, "start_x"))
            right_button = self.create_lane_button("→", lane, lambda idx=index: self.adjust_lane(idx, 5, "start_x"))
            up_button = self.create_lane_button("↑", lane, lambda idx=index: self.adjust_lane(idx, -5, "y"))
            down_button = self.create_lane_button("↓", lane, lambda idx=index: self.adjust_lane(idx, 5, "y"))
            size_plus_button = self.create_lane_button("+", lane, lambda idx=index: self.adjust_lane(idx, 5, "width"))
            size_minus_button = self.create_lane_button("-", lane, lambda idx=index: self.adjust_lane(idx, -5, "width"))

            # Add buttons to the layout
            for button in [left_button, right_button, up_button, down_button, size_plus_button, size_minus_button]:
                lane_layout.addWidget(button)

            # Save references for later updates
            self.lane_controls.append(
                {
                    "checkbox": checkbox,
                    "buttons": [left_button, right_button, up_button, down_button, size_plus_button, size_minus_button],
                }
            )

            # Add the lane layout to the controls layout
            self.controls_layout.addLayout(lane_layout)

    def create_lane_button(self, text, lane, action):
        """Create a button with optional continuous action."""
        button = QtWidgets.QPushButton(text)
        button.setFixedWidth(40)
        button.setEnabled(lane.enabled)

        # Connect the action to button clicks

        def on_press():
            timer.start()
        def on_release():
            timer.stop()
        def perform():
            action()

        button.clicked.connect(perform)
        # Add continuous action support with QTimer
        timer = QtCore.QTimer(self)
        timer.setInterval(100)  # Adjust interval as needed (100ms default)
        timer.timeout.connect(perform)

        button.pressed.connect(on_press)  # Start the timer when pressed
        button.released.connect(on_release)  # Stop the timer when released

        return button

    def add_bottom_buttons(self):
        """Add OK and Cancel buttons at the bottom of the UI."""
        self.ok_button = QtWidgets.QPushButton("OK")
        self.ok_button.setFixedWidth(80)
        self.ok_button.clicked.connect(self.close)

        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.addWidget(self.ok_button)

        self.layout.addLayout(bottom_layout)

    def toggle_lane(self, state, lane, lane_index):
        """Enable or disable a lane."""
        self.lanes[lane_index].enabled = state == QtCore.Qt.Checked
        self.update_controls()
        self.render_frame_with_lanes()

    def update_controls(self):
        """Update the state of lane controls based on enabled lanes."""
        for i, lane in enumerate(self.lanes):
            controls = self.lane_controls[i]
            controls["checkbox"].setChecked(lane.enabled)
            for button in controls["buttons"]:
                button.setEnabled(lane.enabled)

        # Update the lane count label
        enabled_count = sum(1 for lane in self.lanes if lane.enabled)
        self.lane_count_label.setText(f"Enabled Lanes: {enabled_count}")

    def adjust_lane(self, lane_index, adjustment, attribute):
        """Adjust a lane's properties (position or width)."""
        lane = self.lanes[lane_index]
        if not lane.enabled:
            return

        if attribute == "start_x":
            lane.start_x += adjustment
        elif attribute == "y":
            lane.y += adjustment
        elif attribute == "width":
            lane.width = max(10, lane.width + adjustment)

        self.render_frame_with_lanes()

    def render_frame_with_lanes(self):
        """Render the frame with all enabled lanes."""
        frame_copy = self.frame.copy()

        for lane in self.lanes:
            if lane.enabled:
                start_x = lane.start_x
                end_x = start_x + lane.width
                cv2.line(frame_copy, (start_x, lane.y), (end_x, lane.y), lane.color, lane.thickness)

        self.display_frame(frame_copy)

    def display_frame(self, frame):
        """Display the frame in the QLabel."""
        height, width, _ = frame.shape
        scale_factor = 800 / width
        new_width = 800
        new_height = int(height * scale_factor)
        resized_frame = cv2.resize(frame, (new_width, new_height))

        rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
        qt_image = QImage(rgb_frame.data, rgb_frame.shape[1], rgb_frame.shape[0], rgb_frame.strides[0], QImage.Format_RGB888)
        self.frame_label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        """Override closeEvent to emit the lanes data when the window is closed."""
        # Emit the lanes data when the window is closed
        enabled_lanes = [lane for lane in self.lanes if lane.enabled]
        self.lanes_passed.emit(enabled_lanes)
        event.accept()
