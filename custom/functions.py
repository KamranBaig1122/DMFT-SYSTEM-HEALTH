# from custom.import_modules import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from sklearn.cluster import DBSCAN
from torchvision.ops import box_iou
import secrets
import hashlib

def generate_secret_key():
    random_bytes = secrets.token_bytes(32)
    secret_key = hashlib.sha256(random_bytes).hexdigest() * 2
    return secret_key



class_names = ['Decayed', 'Missing', 'Filled']

def cluster_boxes_with_dbscan(boxes, eps=0.8, min_samples=1):
    if boxes.size(0) == 0:
        return np.array([])
    iou_matrix = box_iou(boxes, boxes).cpu().numpy()
    distance_matrix = 1 - iou_matrix
    dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
    cluster_labels = dbscan.fit_predict(distance_matrix)
    return cluster_labels


def visualize_predictions(image, boxes, labels, scores, output_path):
    fig, ax = plt.subplots(1)
    ax.axis('off')
    ax.imshow(image)

    for i, box in enumerate(boxes):
        x_min, y_min, x_max, y_max = box
        rect = patches.Rectangle((x_min, y_min), x_max - x_min, y_max - y_min,
                                 linewidth=2, edgecolor='r', facecolor='none')
        ax.add_patch(rect)

        # if int(labels[i]) < len(class_names):
        #     if int(labels[i]) == 1:
        #         class_label = "Decayed"
        #     else:
        #         class_label = class_names[int(labels[i])]
        # else:
        #     class_label = "Filled"
        if int(labels[i]) < len(class_names):
            class_label = class_names[int(labels[i])]
        else:
            class_label = "Unknown"  
        confidence_score = scores[i]
        ax.text(x_min, y_min - 10, f'{class_label}: {confidence_score:.2f}', color='red', fontsize=10, backgroundcolor='white')

    plt.savefig(output_path, bbox_inches='tight', pad_inches=0)
    plt.close(fig)


def filter_valid_labels(boxes, labels, scores):
            valid_indices = (labels >= 0) & (labels <= 2)
            return boxes[valid_indices], labels[valid_indices], scores[valid_indices]