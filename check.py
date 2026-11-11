import cv2
from ultralytics import YOLO

cap = cv2.VideoCapture("data/packing.mp4")
print("fps:", cap.get(cv2.CAP_PROP_FPS), "frames:", int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
ok, frame = cap.read()
cv2.imwrite("data/frame.jpg", frame)

res = YOLO("yolov8n-pose.pt")(frame)[0]   # downloads the weights on first run
print("people:", len(res.boxes), "keypoints shape:", tuple(res.keypoints.xy.shape))