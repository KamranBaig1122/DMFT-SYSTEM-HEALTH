# DMFT Detection System

A web-based dental health analysis system that automatically detects and analyzes dental conditions using advanced computer vision and machine learning technologies. The system identifies decayed, missing, and filled teeth from dental X-ray images and calculates the DMFT (Decayed, Missing, Filled Teeth) index.

## What This Project Does

The DMFT Detection System is a Flask-based web application designed for dental professionals and patients to:

- **Automated Tooth Detection**: Upload dental X-ray images and automatically detect dental conditions using state-of-the-art YOLO (You Only Look Once) object detection models (YOLOv10 and YOLOv11) also faster-RCNN model
- **DMFT Index Calculation**: Automatically calculate the DMFT index by counting:
  - **Decayed teeth** (D)
  - **Missing teeth** (M)
  - **Filled teeth** (F)
  - **Total DMFT index** (sum of all detected conditions)
- **Image Analysis**: Process multiple dental images (up to 5 at a time) and generate annotated visualizations showing detected dental conditions
- **Patient Data Management**: Store and manage patient records with their DMFT analysis results in a MongoDB database
- **User Management**: Support for multiple user roles:
  - **Doctors**: Can analyze images, save patient data, and view their patient records
  - **Patients**: Can access the system and view their dental health information
  - **Administrators**: Can manage all users, view all patient records, and access system-wide statistics
- **Secure Authentication**: User registration and login system with password hashing and session management
- **Results Visualization**: View detailed analysis results with annotated images showing detected dental conditions

## Key Features

- Three models integration YOLOv10, YOLOv11 and Faster RCNN for enhanced detection accuracy
- DBSCAN clustering algorithm to merge overlapping detections
- Real-time image processing and analysis
- Secure user authentication and authorization
- Patient data storage and retrieval
- Admin dashboard for system management
- Responsive web interface for easy access

This system helps dental professionals efficiently assess oral health conditions and maintain comprehensive patient records for better dental care management.
