import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from ocr_engine import parse_prescription

def test_parsing():
    sample_text = "Dr. John Doe. Date: 12/12/2023. Rx: Metformin 500mg OD after food. Amlodipine 5mg 1-0-1. Atorvastatin 10mg Once a day."
    print(f"Sample Text: {sample_text}")
    
    results = parse_prescription(sample_text)
    
    print("\nExtracted Medicines:")
    for res in results:
        print(res)

if __name__ == "__main__":
    test_parsing()
