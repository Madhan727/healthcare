import requests
from fuzzywuzzy import process
import json
import os

# Load local knowledge base for fuzzy matching first
# In production, this list would be larger or fetched from DB
LOCAL_MEDICINES = [
    "Metformin", "Amlodipine", "Atorvastatin", "Lisinopril", "Levothyroxine",
    "Losartan", "Omeprazole", "Paracetamol", "Amoxicillin", "Ibuprofen", 
    "Aspirin", "Simvastatin", "Gabapentin", "Hydrochlorothiazide"
]

OPENFDA_URL = "https://api.fda.gov/drug/label.json"

def normalize_name(name):
    """
    Normalizes medicine name using fuzzy matching against a known list.
    """
    if not name:
        return None
    
    # Simple cleanup
    clean_name = name.strip().capitalize()
    
    # Fuzzy Match
    match, score = process.extractOne(clean_name, LOCAL_MEDICINES)
    
    if score > 80:
        return match
    return clean_name # Return original if no good match

def fetch_drug_info(medicine_name):
    """
    Fetches drug information from OpenFDA API.
    """
    try:
        # Search by brand_name or generic_name
        query = f'openfda.brand_name:"{medicine_name}"+OR+openfda.generic_name:"{medicine_name}"'
        response = requests.get(f"{OPENFDA_URL}?search={query}&limit=1")
        
        if response.status_code == 200:
            data = response.json()
            if 'results' in data:
                result = data['results'][0]
                
                # Extract key fields safely
                info = {
                    "generic_name": result.get('openfda', {}).get('generic_name', ['Unknown'])[0],
                    "purpose": result.get('purpose', ['Not specified'])[0],
                    "warnings": result.get('warnings', ['None'])[0][:200] + "...",
                    "indications": result.get('indications_and_usage', ['Not specified'])[0][:200] + "...",
                    "source": "OpenFDA"
                }
                return info
    except Exception as e:
        print(f"Error fetching drug info for {medicine_name}: {e}")
    
    # Fallback to local
    return {
        "generic_name": medicine_name,
        "purpose": "Consult Doctor",
        "warnings": "No data available",
        "source": "Local"
    }
