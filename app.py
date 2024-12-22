from flask import Flask, Response, request, jsonify
from flask_cors import CORS
import easyocr
from io import BytesIO
from PIL import Image, ImageOps
import json
import os
import cv2
import numpy as np

# Make debug folder if it does not exist
os.makedirs("./debug", exist_ok=True)

app = Flask(__name__)

# Initialize the OCR reader globally to avoid repeated initialization
reader = easyocr.Reader(['ja'], gpu=False)

# Enable CORS for all routes and all methods
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})

@app.route('/ocr_local', methods=['POST'])
def ocr_local():
    try:
        # Step 1: Load the image
        file = request.files.get('image')
        if not file:
            print("Error: No image provided.")
            return jsonify({"error": "No file provided"}), 400

        image = Image.open(file.stream)
        image.save("./debug/original_uploaded_image.png")

        # Step 2: Normalize EXIF orientation
        image = ImageOps.exif_transpose(image)
        image.save("./debug/exif_corrected_image.png")

        # Step 3: Convert to grayscale and binarize
        image = ImageOps.grayscale(image)
        image.save("./debug/after_grayscale_image.png")

        image_array = np.array(image)
        _, binary_image = cv2.threshold(image_array, 128, 255, cv2.THRESH_BINARY)
        final_image = Image.fromarray(binary_image)
        final_image.save("./debug/final_binarized_image.png")

        # Step 4: OCR logic
        orientation = request.form.get('orientation', 'horizontal')
        print(f"Orientation received: {orientation}")
        if orientation == 'vertical':
            print("Processing vertical image.")
            results = process_vertical_lines_with_detection(final_image)
        else:
            print("Processing horizontal image.")
            results = reader.readtext(np.array(final_image), detail=0)

        print(f"OCR Results: {results}")
        return jsonify({"text": results})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def detect_text_regions(image):
    """Detect regions containing text using contours."""
    image_array = np.array(image)

    # Find contours
    contours, _ = cv2.findContours(image_array, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter out regions based on size
    text_regions = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 5 and h > 20:  # Adjusted thresholds for vertical text
            text_regions.append((x, y, w, h))

    # Sort regions from top to bottom
    text_regions = sorted(text_regions, key=lambda r: r[1])
    print(f"Detected text regions: {text_regions}")
    return text_regions

def process_vertical_lines_with_detection(image):
    """Process vertical text by detecting regions."""
    text_regions = detect_text_regions(image)
    print(f"Detected text regions for vertical text: {text_regions}")

    results = []
    for idx, (x, y, w, h) in enumerate(text_regions):
        # Crop the region
        region = image.crop((x, y, x + w, y + h))
        region.save(f"./debug/vertical_crop_{idx}.png")
        print(f"Saved cropped region {idx} to ./debug/vertical_crop_{idx}.png")

        # Convert to binary and perform OCR
        region_array = np.array(region)
        _, binary_region = cv2.threshold(region_array, 128, 255, cv2.THRESH_BINARY)
        binary_image = Image.fromarray(binary_region)
        text = reader.readtext(np.array(binary_image), detail=0)
        print(f"OCR result for region {idx}: {text}")

        # Append all detected text to results
        if text:
            results.extend(text)  # Append all detected text items instead of just the first one

    # Return results as a list to ensure consistent format
    return results


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
