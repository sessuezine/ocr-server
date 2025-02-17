# OCR Server

**A Flask-based OCR server utilizing EasyOCR for text extraction from images.**

## 🚀 Overview

This OCR (Optical Character Recognition) server processes images to extract text using the EasyOCR engine. Built with Flask, it offers an API for uploading images and retrieving the extracted text, making it suitable for applications like document processing and automation workflows.

## 🛠 Features

- **EasyOCR Integration** – Uses EasyOCR for robust text extraction.
- **RESTful API** – Accepts images via `POST` requests and returns extracted text in JSON format.
- **CORS Enabled** – Supports Cross-Origin Resource Sharing for flexible integration.
- **Debug Mode** – Saves processed images to a `debug/` folder for inspection.

## ⚡ Installation

### Prerequisites

- **Python 3.x** – Ensure Python is installed on your system.
- **pip** – Python package installer.

### Steps

1. **Clone the Repository**:  
   `git clone https://github.com/sessuezine/ocr-server.git && cd ocr-server`

2. **Set Up a Virtual Environment** (optional but recommended):  
   `python -m venv venv && source venv/bin/activate` (For Windows: `venv\Scripts\activate`)

3. **Install Dependencies**:  
   `pip install -r requirements.txt`

4. **Install OpenCV**:  
   - **Ubuntu/Debian**: `sudo apt-get install python3-opencv`  
   - **macOS** (Homebrew): `brew install opencv`  
   - **Windows**: `pip install opencv-python-headless`

5. **Run the Server**:  
   `python app.py`  
   The server will start at `http://127.0.0.1:5000/`.

## 📡 API Usage

### Endpoint

- `POST /ocr`

### Request

- **Headers**: `Content-Type: multipart/form-data`
- **Body**: Form-data with an `image` file field.

### Response

- **Success (`200 OK`)**:  
  ```json
  {
    "text": "Extracted text from the image."
  }
