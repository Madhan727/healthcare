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
        # data is now in app/data
        base_dir = os.path.dirname(os.path.dirname(__file__)) # src/.. -> health root
        json_path = os.path.join(base_dir, 'app', 'data', 'medicines.json')
        with open(json_path, 'r') as f:
            data = json.load(f)
            known_medicines = list(data.get('medicines', {}).keys())
    except Exception:
        pass

    # fuzzy logic for better detection
    from fuzzywuzzy import process
    
    # Split text into lines to maintain some context
    lines = text.split('\n')
    # If single line, split by spaces but keep chunks
    if len(lines) < 2:
        lines = [text]

    for line in lines:
        # Split by non-alphanumeric to handle "Metforrr500mg" or "Metformin-500"
        words = re.split(r'[^a-zA-Z0-9]+', line)
        # Sliding window for multi-word medicines (e.g. "Metformin HCL")
        for i in range(len(words)):
            # Check single word
            word = words[i]
            # Check 2-word phrase
            phrase = " ".join(words[i:i+2]) if i+1 < len(words) else ""
            
            candidates = [word]
            if phrase: candidates.append(phrase)
            
            for cand in candidates:
                # Clean candidate
                clean_cand = re.sub(r'[^a-zA-Z\s]', '', cand).strip()
                if len(clean_cand) < 3: continue
                
                # Loose Fuzzy Match against knownDB
                match, score = process.extractOne(clean_cand, known_medicines)
                
                if score >= 70: # Lowered threshold further for better resilience (e.g. Metforrr=71)
                    # Avoid duplicates
                    if not any(m['name'] == match for m in medicines):
                        # Look for dosage/freq in the full line
                        dosage = dosage_pattern.search(line)
                        freq = freq_pattern.search(line)
                        
                        medicines.append({
                            "name": match,
                            "dosage": dosage.group(0) if dosage else "Unknown",
                            "frequency": freq.group(0) if freq else "Unknown"
                        })
    return medicines
