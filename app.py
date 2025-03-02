from flask import Flask, render_template, request, jsonify
import requests
import os
import json
import difflib
from werkzeug.utils import secure_filename
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Load API Key from environment variable
API_KEY = os.environ.get("PLANT_ID_API_KEY", "FRSaEd1HFSWGj7pWbTBuvlM1AK5HC4GPxy7fC1NEpmwdSQXGtv")
API_URL = "https://api.plant.id/v2/identify"

# Set upload folder for images
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    """Check if the uploaded file is an allowed image."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Load non-weed plants from a text file
def load_non_weed_plants(filename='non-weed.txt'):
    try:
        with open(filename, 'r') as file:
            return {line.strip().lower() for line in file if line.strip()}
    except FileNotFoundError:
        print(f"⚠️ Warning: {filename} not found.")
        return set()

# Load known weeds from a JSON file
def load_weed_data(filename='Weed_info.json'):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"⚠️ Warning: {filename} not found or invalid.")
        return []

# Initialize data once at startup
NON_WEED_PLANTS = load_non_weed_plants()
WEED_DATA = load_weed_data()

# Fuzzy matching function
def find_best_match(plant_name, weed_list):
    """Find the closest matching plant name from a list using fuzzy matching."""
    plant_name_lower = plant_name.lower()
    matches = difflib.get_close_matches(plant_name_lower, [w.get('WeedType', '').lower() for w in weed_list if 'WeedType' in w], n=1, cutoff=0.8)
    
    if matches:
        for weed in weed_list:
            if weed.get('WeedType', '').lower() == matches[0]:
                return weed  # Return full weed data if a match is found
    return None

@app.route('/')
def index():
    """Homepage for uploading images."""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Handle image upload and weed identification."""
    # Check if file is in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'})

    file = request.files['file']
    
    # Check if file is empty
    if file.filename == '':
        # Handle camera capture case (no filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"capture_{timestamp}.jpg"
    else:
        # Handle regular file upload
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file format'})
        filename = secure_filename(file.filename)
    
    # Save the file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Call Plant.id API
    with open(filepath, 'rb') as img_file:
        response = requests.post(
            API_URL,
            headers={'Api-Key': API_KEY},
            files={'images': img_file},
            data={'organs': 'leaf'}
        )

    if response.status_code == 200:
        try:
            result = response.json()
            if 'suggestions' in result and len(result['suggestions']) > 0:
                top_suggestion = result['suggestions'][0]
                plant_name = top_suggestion['plant_name'].strip()
                confidence = top_suggestion['probability'] * 100

                # Check against non-weed plants
                if plant_name.lower() in NON_WEED_PLANTS:
                    return jsonify({
                        'PlantName': plant_name,
                        'Confidence': f"{confidence:.2f}%",
                        'isWeed': False,
                        'Message': "This is not a weed.",
                        'ImagePath': f"/static/images/{filename}"
                    })

                # Check against known weeds using fuzzy matching
                matched_weed = find_best_match(plant_name, WEED_DATA)
                if matched_weed:
                    return jsonify({
                        'PlantName': plant_name,
                        'Confidence': f"{confidence:.2f}%",
                        'isWeed': True,
                        'Message': matched_weed.get('Message', 'This is identified as a weed.'),
                        'ControlMeasure': matched_weed.get('ControlMeasure', 'No control measures available.'),
                        'Climate': matched_weed.get('Climate', 'Climate information not available.'),
                        'AdditionalInfo': matched_weed.get('AdditionalInfo', 'No additional information available.'),
                        'MoreDetails': matched_weed.get('MoreDetails', 'No additional details available.'),
                        'ImagePath': f"/static/images/{filename}"
                    })

                # Default case: Not identified as a weed or a known non-weed
                return jsonify({
                    'PlantName': plant_name,
                    'Confidence': f"{confidence:.2f}%",
                    'isWeed': False,
                    'Message': "Plant is not identified as a weed or a known non-weed.",
                    'ImagePath': f"/static/images/{filename}"
                })
            else:
                return jsonify({'error': 'No plant detected in the image'})
        except ValueError:
            return jsonify({'error': 'Invalid response from API'})
    else:
        return jsonify({
            'error': 'API request failed',
            'status_code': response.status_code,
            'details': response.text
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)