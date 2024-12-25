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
        # _, binary_image = cv2.threshold(image_array, 128, 255, cv2.THRESH_BINARY)
        final_image = image
        # final_image.save("./debug/final_binarized_image.png")

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
    """Detect text regions directly from the grayscale image without binarization."""
    image_array = np.array(image)

    # Use adaptive thresholding to better separate text regions
    binary_image = cv2.adaptiveThreshold(
        image_array,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=11,
        C=2
    )

    # Find contours
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    text_regions = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 5 and h > 10:  # Adjust thresholds for smaller regions
            text_regions.append((x, y, w, h))

    print(f"Detected text regions: {text_regions}")
    return text_regions

def split_large_regions(image, region, min_char_width=10, min_char_height=10):
    """Split a large text region into smaller ones based on pixel intensity."""
    x, y, w, h = region
    subregions = []

    # Crop the region
    cropped_region = np.array(image.crop((x, y, x + w, y + h)))

    # Compute vertical projection (histogram)
    vertical_projection = np.sum(cropped_region, axis=0)
    split_points = []  # Track splitting positions

    for i in range(1, len(vertical_projection)):
        if vertical_projection[i] == 0 and vertical_projection[i - 1] > 0:
            split_points.append(i)

    # Define subregions based on split points
    prev_split = 0
    for split in split_points:
        if split - prev_split >= min_char_width:
            subregions.append((x + prev_split, y, split - prev_split, h))
        prev_split = split

    # Include the last region
    if w - prev_split >= min_char_width:
        subregions.append((x + prev_split, y, w - prev_split, h))

    return subregions


def process_vertical_lines_with_detection(image):
    """Process vertical text by detecting regions with dynamic padding."""
    text_regions = detect_text_regions(image)
    print(f"Detected text regions for vertical text: {text_regions}")

    results = []

    for idx, (x, y, w, h) in enumerate(text_regions):
        # Calculate dynamic padding based on region size
        base_padding = int(min(w, h) * 0.2)  # 20% of the smaller dimension
        density_padding = estimate_density_padding(image, x, y, w, h)
        dynamic_padding = max(base_padding, density_padding)  # Choose the larger padding

        # Adjust coordinates with dynamic padding
        padded_x = max(x - dynamic_padding, 0)
        padded_y = max(y - dynamic_padding, 0)
        padded_w = min(w + 2 * dynamic_padding, image.width - padded_x)
        padded_h = min(h + 2 * dynamic_padding, image.height - padded_y)

        # Crop the region with dynamic padding
        region = image.crop((padded_x, padded_y, padded_x + padded_w, padded_y + padded_h))
        region.save(f"./debug/vertical_crop_{idx}.png")
        print(f"Saved cropped region {idx} to ./debug/vertical_crop_{idx}.png")

        # Perform OCR directly
        text = reader.readtext(np.array(region), detail=0)
        print(f"OCR result for region {idx}: {text}")

        # Append all detected text to results
        if text:
            results.extend(text)

    return results

def estimate_density_padding(image, x, y, w, h):
    """Estimate additional padding based on the pixel density near the region's edges."""
    image_array = np.array(image)

    # Define edge regions for density analysis
    top_edge = image_array[max(y - 5, 0):y, x:x + w]
    bottom_edge = image_array[y + h:min(y + h + 5, image_array.shape[0]), x:x + w]
    left_edge = image_array[y:y + h, max(x - 5, 0):x]
    right_edge = image_array[y:y + h, x + w:min(x + w + 5, image_array.shape[1])]

    # Compute average intensity in edge regions (lower intensity = denser text)
    edge_intensities = [
        np.mean(top_edge) if top_edge.size > 0 else 255,
        np.mean(bottom_edge) if bottom_edge.size > 0 else 255,
        np.mean(left_edge) if left_edge.size > 0 else 255,
        np.mean(right_edge) if right_edge.size > 0 else 255,
    ]

    # Calculate density-based padding: lower intensity leads to higher padding
    density_factor = 10  # Adjust as needed to scale the padding
    min_intensity = min(edge_intensities)
    density_padding = max(0, int(density_factor * (255 - min_intensity) / 255))  # Normalize to a max value

    return density_padding


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
