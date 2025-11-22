# from custom.functions import *
from custom.functions import *
import torch
import os
import warnings
from ultralytics import YOLO

# Suppress warnings during model loading
warnings.filterwarnings("ignore", category=UserWarning)


device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../static/uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../static/uploads/output')

yolo_model_v10_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../static/models/yolo/yolov10.pt')
yolo_model_v11_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../static/models/yolo/yolov11.pt')

yolo_model_v10 = YOLO(yolo_model_v10_path).to(device)
yolo_model_v11 = YOLO(yolo_model_v11_path).to(device)

confidence_threshold_yolo = 0.3