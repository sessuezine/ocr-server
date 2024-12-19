from flask import Flask, Response, request, jsonify
from flask_cors import CORS
import easyocr
from io import BytesIO
from PIL import Image, ImageOps
import json

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


@app.route('/ocr_local', methods=['POST'])
def ocr_local():
    try:
        # Get the uploaded file
        file = request.files.get('image')
        if not file:
            return jsonify({"error": "No file provided"}), 400

        # Open the image using PIL
        image = Image.open(file.stream)

        # Convert to grayscale
        image = ImageOps.grayscale(image)

        # Convert the PIL image to bytes
        image_bytes = BytesIO()
        image.save(image_bytes, format='PNG')  # Save as PNG
        image_bytes = image_bytes.getvalue()

        # Perform OCR
        reader = easyocr.Reader(['ja'], gpu=False)
        results = reader.readtext(image_bytes, detail=0)

        # Prepare the response
        response_data = {"text": results}

        # Return unescaped JSON
        return Response(
            json.dumps(response_data, ensure_ascii=False),
            content_type="application/json; charset=utf-8"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500




# Print all registered routes
print("\nRegistered Routes:")
for rule in app.url_map.iter_rules():
    print(f"Route: {rule} -> {rule.endpoint}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
