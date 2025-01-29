from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from dataclasses import dataclass
import cv2
from Lane import Lane


class LaneAdjustmentApp(QtWidgets.QWidget):
    lanes_passed = pyqtSignal(list)  # Define the signal
    # window_closed = pyqtSignal()

    def __init__(self, frame, parent=None):
        super().__init__(parent)
        self.previous_x = None
        self.is_dragging = False
        self.offset_x = 0
        self.dragged_lane = None
        self.frame = frame
        self.frame_height = frame.shape[0]
        self.frame_width = frame.shape[1]

        # Initialize lanes
        self.lanes = [
            Lane(
                start_x=100 + (i * 60),
                width=50,
                enabled=(i == 0),
                y=(self.frame_height - (self.frame_height // 3)) + 1,
                color=Lane.color(i),
                direction="in" if i < 4 else "out"  # First 4 lanes = "in", rest = "out"
            )
            for i in range(8)
        ]

        self.crossing = Lane(
            start_x=0,
            width=self.frame_width,
            enabled=True,
            y=self.frame_height - (self.frame_height // 3),
            color=(65, 70, 84),
            name="crossing",
            thickness=10,
            direction="center"
        )

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
        self.frame_label.setFixedSize(800, 500)
        self.layout.addWidget(self.frame_label)

        # Lane Controls Layout
        self.controls_layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.controls_layout)

        # Lane Count Label
        self.lane_count_label = QtWidgets.QLabel("Enabled Lanes: 1")
        self.layout.addWidget(self.lane_count_label)

        # Create controls for all lanes
        self.create_lane_controls()
        self.create_crossing_control()

        # Buttons for finalizing or canceling
        self.add_bottom_buttons()

        self.setLayout(self.layout)

    def create_lane_controls(self):
        """Create controls for all lanes and add them to the UI."""

        # Add "IN only" label above the first 4 lanes
        in_label = QtWidgets.QLabel("IN only")
        in_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.controls_layout.addWidget(in_label)

        for index, lane in enumerate(self.lanes[:4]):  # First 4 lanes (IN)
            lane_layout = QtWidgets.QHBoxLayout()
            self.add_lane_control(index, lane, lane_layout)
            self.controls_layout.addLayout(lane_layout)

        # Add "OUT only" label above the last 4 lanes
        out_label = QtWidgets.QLabel("OUT only")
        out_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        self.controls_layout.addWidget(out_label)

        for index, lane in enumerate(self.lanes[4:], start=4):  # Last 4 lanes (OUT)
            lane_layout = QtWidgets.QHBoxLayout()
            self.add_lane_control(index, lane, lane_layout)
            self.controls_layout.addLayout(lane_layout)

    def add_lane_control(self, index, lane, lane_layout):
        """Helper function to add controls for a single lane."""

        # Checkbox to enable/disable the lane
        checkbox = QtWidgets.QCheckBox(f"Lane {index + 1}")
        checkbox.setChecked(lane.enabled)
        checkbox.stateChanged.connect(lambda state, l=lane, idx=index: self.toggle_lane(state, l, idx))
        lane_layout.addWidget(checkbox)

        left_button = self.create_lane_button("←", lane, lambda idx=index: self.adjust_lane(idx, -15, "start_x"))
        right_button = self.create_lane_button("→", lane, lambda idx=index: self.adjust_lane(idx, 15, "start_x"))
        size_plus_button = self.create_lane_button("+", lane, lambda idx=index: self.adjust_lane(idx, 15, "width"))
        size_minus_button = self.create_lane_button("-", lane, lambda idx=index: self.adjust_lane(idx, -15, "width"))

        # Add buttons to the layout
        for button in [left_button, right_button, size_plus_button, size_minus_button]:
            lane_layout.addWidget(button)

        # Save references for later updates
        self.lane_controls.append({
            "checkbox": checkbox,
            "buttons": [left_button, right_button, size_plus_button, size_minus_button],
        })

    def create_crossing_control(self):
        """Create controls for all lanes and add them to the UI."""

        crossing_layout = QtWidgets.QHBoxLayout()

        # Checkbox to enable/disable the lane
        checkbox = QtWidgets.QCheckBox(f"Crossing")
        checkbox.setChecked(True)
        checkbox.setDisabled(True)
        crossing_layout.addWidget(checkbox)

        up_button = self.create_lane_button("↑", self.crossing, lambda idx=0: self.adjust_crossing(-5, "y"))
        down_button = self.create_lane_button("↓", self.crossing, lambda idx=0: self.adjust_crossing(5, "y"))

        # Add buttons to the layout
        for button in [up_button, down_button]:
            crossing_layout.addWidget(button)

        # Save references for later updates
        self.lane_controls.append(
            {
                "checkbox": checkbox,
                "buttons": [up_button, down_button],
            }
        )

        # Add the lane layout to the controls layout
        self.controls_layout.addLayout(crossing_layout)

    def create_lane_button(self, text, lane, action):
        """Create a button with optional continuous action."""
        button = QtWidgets.QPushButton(text)
        button.setFixedWidth(40)
        button.setEnabled(lane.enabled)

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
        if state == QtCore.Qt.Checked:
            # Find the last enabled lane before this one
            prev_enabled_lane = None
            for i in range(lane_index - 1, -1, -1):
                if self.lanes[i].enabled:
                    prev_enabled_lane = self.lanes[i]
                    break

            # Set start_x based on the previous enabled lane
            if prev_enabled_lane:
                lane.start_x = prev_enabled_lane.start_x + prev_enabled_lane.width

            lane.enabled = True
        else:
            lane.enabled = False

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

    def adjust_crossing(self, adjustment, attribute):
        """Adjust a lane's properties (position or width)."""

        if attribute == "y":
            for lane in self.lanes:
                lane.y += adjustment
            self.crossing.y += adjustment

        self.render_frame_with_lanes()

    def render_frame_with_lanes(self):
        """Render the frame with all enabled lanes."""
        frame_copy = self.frame.copy()

        # for lane in self.lanes:
        #     if lane.enabled:
        #         lane_rect = QtCore.QRect(lane.start_x, lane.y, lane.width, 50)  # Horizontal lane hitbox
        #         # Draw the hitbox as a semi-transparent rectangle (for visualization)
        #         cv2.rectangle(frame_copy,
        #                       (lane_rect.left(), lane_rect.top()),
        #                       (lane_rect.right(), lane_rect.bottom()),
        #                       (255, 0, 0), 2)  # Red color, 2px thickness
        # if self.crossing.enabled:
        #     self.crossing.draw(frame_copy)
        for lane in self.lanes:
            if lane.enabled:
                lane.draw(frame_copy)

        self.display_frame(frame_copy)

    def display_frame(self, frame):
        """Display the frame in the QLabel."""
        height, width, _ = frame.shape
        scale_factor = 800 / width
        new_width = 800
        new_height = int(height * scale_factor)
        resized_frame = cv2.resize(frame, (new_width, new_height))

        rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
        qt_image = QImage(rgb_frame.data, rgb_frame.shape[1], rgb_frame.shape[0], rgb_frame.strides[0],
                          QImage.Format_RGB888)
        self.frame_label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        """Override closeEvent to emit the lanes data when the window is closed."""
        # Emit the lanes data when the window is closed
        enabled_lanes = [lane for lane in self.lanes if lane.enabled]
        enabled_lanes.append(self.crossing)
        self.lanes_passed.emit(enabled_lanes)
        # self.window_closed.emit()
        event.accept()
