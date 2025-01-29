import random
from dataclasses import dataclass

import cv2


@dataclass
class Lane:
    start_x: int
    width: int
    color: tuple
    enabled: bool = False
    y: int = 0
    thickness: int = 5
    name: str = "lane"

    def draw(self, frame):
        end = self.start_x + self.width
        cv2.line(frame, (self.start_x, self.y), (end, self.y), self.color, self.thickness)

    def blink(self, frame):
        end = self.start_x + self.width
        cv2.line(frame, (self.start_x, self.y), (end, self.y), (255, 255, 255), self.thickness)

    def blink_dark(self, frame):
        end = self.start_x + self.width
        cv2.line(frame, (self.start_x, self.y), (end, self.y), (10, 10, 10), self.thickness)

    def start(self):
        return self.start_x, self.y

    def end(self):
        return self.start_x + self.width, self.y

    @staticmethod
    def color(idx):
        lst = [
            (255, 0, 0),  # Red
            (0, 255, 0),  # Green
            (0, 0, 255),  # Blue
            (0, 255, 255),  # Cyan
            (255, 0, 255),  # Magenta
            (255, 255, 0),  # Yellow
            (138, 43, 226),  # Violet
            (247, 141, 187)  # Cream
        ]
        return lst[idx]
