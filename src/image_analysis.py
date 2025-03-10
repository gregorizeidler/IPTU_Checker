import cv2
import numpy as np
import torch
from ultralytics import YOLO

# Load YOLO model for detecting land structures
model = YOLO("yolov8n.pt")

def process_image(image_path):
    """Process satellite images to identify land and building boundaries."""
    img = cv2.imread(image_path)
    results = model(img)
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
    cv2.imshow("Land Analysis", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
