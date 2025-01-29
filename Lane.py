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
    def generate_color():
        # Random bright colors are typically in the higher range of RGB values
        r = random.randint(128, 255)
        g = random.randint(200, 255)
        b = random.randint(128, 255)
        return r, g, b
