from flask import Flask, Response, request, jsonify
from flask_cors import CORS
import easyocr
from io import BytesIO
from PIL import Image, ImageOps
import json
import os 

# Make debug folder if it does not exist
os.makedirs("./debug", exist_ok=True)

import requests

app = Flask(__name__)

# Initialize the OCR reader globally to avoid repeated initialization
reader = easyocr.Reader(['ja'], gpu=False)

# Enable CORS for all routes and all methods
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})

@app.route("/")
def home():
    return "Flask server is running with CORS enabled!"

@app.route('/ocr', methods=['POST'])
def ocr():
    try:
        data = request.json
        image_url = data.get('image_url')

        if not image_url:
            return jsonify({"error": "No image_url provided"}), 400

        # Fetch the image
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))

        # Perform OCR
        results = reader.readtext(image, detail=0)

        return jsonify({"text": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ocr_local', methods=['POST'])
def ocr_local():
    try:
        # Get the uploaded file
        file = request.files.get('image')
        if not file:
            return jsonify({"error": "No file provided"}), 400
        
        # Save the uploaded file for debugging
        file.save("./debug/uploaded_image.png")

        # Open the image using PIL
        image = Image.open(file.stream)

        # Retrieve orientation from the request (sent from the frontend)
        orientation = request.form.get('orientation', 'horizontal')

        # Rotate if vertical orientation is detected
        rotation_angle = 90 if orientation == 'vertical' else 0
        if rotation_angle:
            image = image.rotate(rotation_angle, expand=True)

        # Save the rotated image for debugging
        image.save(f"./debug/rotated_image_{orientation}.png")

        # Convert to grayscale
        image = ImageOps.grayscale(image)

        # Convert the PIL image to bytes
        image_bytes = BytesIO()
        image.save(image_bytes, format='PNG')  # Save as PNG
        image_bytes = image_bytes.getvalue()

        # Perform OCR
        results = reader.readtext(image_bytes, detail=0)

        # Prepare the response
        response_data = {"text": results}

        # Return unescaped JSON
        return Response(
            json.dumps(response_data, ensure_ascii=False),
            content_type="application/json; charset=utf-8"
        )
    except Exception as e:
        # Log the error for debugging
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def process_vertical_text(image, character_height):
    width, height = image.size
    results = []
    for top in range(0, height, character_height):
        box = (0, top, width, min(top + character_height, height))
        char_crop = image.crop(box)
        text = reader.readtext(char_crop, detail=0)
        results.append(text[0] if text else "")
    return "".join(results)


# Print all registered routes
print("\nRegistered Routes:")
for rule in app.url_map.iter_rules():
    print(f"Route: {rule} -> {rule.endpoint}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
