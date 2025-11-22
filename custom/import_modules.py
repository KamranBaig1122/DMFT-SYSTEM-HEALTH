import matplotlib
import glob
from PIL import Image
from werkzeug.utils import secure_filename
import json
import cv2
from werkzeug.security import generate_password_hash, check_password_hash
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from flask_wtf import CSRFProtect
from flask import Flask
from custom.mongodb_config import mongodb_models
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv

matplotlib.use('Agg')

# Load environment variables
load_dotenv('config.env')