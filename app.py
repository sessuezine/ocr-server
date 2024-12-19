from flask import Flask, request, jsonify
from flask_cors import CORS
import easyocr
import requests
from io import BytesIO
from PIL import Image

app = Flask(__name__)
# Enable CORS for all routes and all methods
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

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
        reader = easyocr.Reader(['ja'], gpu=False)
        results = reader.readtext(image, detail=0)

        return jsonify({"text": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

