import easyocr
import cv2
import numpy as np
import re

def extract_text(image_path):
    """
    Extracts text from an image using EasyOCR with enhanced preprocessing.
    """
    # Preprocessing
    image = cv2.imread(image_path)
    if image is None:
        return ""
    
    # 1. Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 2. Denoising
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # 3. Adaptive Thresholding (Smart OCR)
    # Binary thresholding to separate text from background
    thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    
    # 4. Optional: Dilation to connect broken text
    # kernel = np.ones((1, 1), np.uint8)
    # dilated = cv2.dilate(thresh, kernel, iterations=1)
    
    # Use the processed image for OCR
    reader = easyocr.Reader(['en'])
    # detail=0 returns just the list of text strings
    result = reader.readtext(thresh, detail=0) 
    
    # Join text with spaces
    text = " ".join(result)
    return text

def parse_prescription(text):
    """
    Parses the extracted text to identify medicines, dosage, and frequency.
    """
    medicines = []
    
    # Common dosage patterns: 500mg, 10 mg, 5ml, etc.
    dosage_pattern = re.compile(r'(\d+\s*(?:mg|ml|g|mcg))', re.IGNORECASE)
    
    # Common frequency patterns: 1-0-1, OD, BD, TID, Twice a day
    freq_pattern = re.compile(r'(1-0-1|0-1-0|1-0-0|0-0-1|OD|BD|TID|BID|QID|Twice a day|Once a day)', re.IGNORECASE)
    
    # Split text into lines or segments based on keywords/spacing could be tricky with just " ".join
    # But often prescriptions have Medicine Name ... Dosage ... Frequency
    # For this simplified version, we will look for known medicines from our DB or just capitalize words followed by dosage
    
    # Let's load known medicines (in a real app this would be efficient, here just reading json for simplicity)
    # NOTE: In production, pass this as an argument or load once.
    import json
    import os
    
    known_medicines = []
    try:
        with open(os.path.join('data', 'medicines.json'), 'r') as f:
            data = json.load(f)
            known_medicines = list(data.get('medicines', {}).keys())
    except Exception:
        pass

    # Simple keyword matching for demo
    words = text.split()
    for i, word in enumerate(words):
        # Clean word
        clean_word = re.sub(r'[^a-zA-Z]', '', word)
        
        # Check against known medicines (case-insensitive for robustness)
        match = next((m for m in known_medicines if m.lower() == clean_word.lower()), None)
        
        if match:
            # Look ahead for dosage and frequency
            context = " ".join(words[i:i+5]) # simple window
            
            dosage = dosage_pattern.search(context)
            freq = freq_pattern.search(context)
            
            medicines.append({
                "name": match,
                "dosage": dosage.group(0) if dosage else "Unknown",
                "frequency": freq.group(0) if freq else "Unknown"
            })
            
    return medicines
