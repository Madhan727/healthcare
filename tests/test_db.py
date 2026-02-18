import sys
import os
import json

sys.path.append(os.path.join(os.getcwd(), 'src'))

from database import init_db, save_patient_record, get_all_patients, get_disease_map

def test_db():
    print("Testing Database...")
    init_db()
    
    # Test Mapping
    print("Testing Disease Mapping...")
    mapping = get_disease_map()
    print(f"Mapping: {mapping}")
    assert "Metformin" in mapping, "Metformin not found in mapping"
    
    # Test Save
    print("Testing Save Patient...")
    patient_data = {
        "name": "Test Patient",
        "medicines": ["Metformin", "Amlodipine"],
        "diseases": ["Diabetes", "Hypertension"],
        "risk_score": 0.15
    }
    save_patient_record(patient_data)
    
    # Test Retrieve
    print("Testing Retrieve...")
    patients = get_all_patients()
    assert len(patients) > 0, "No patients found"
    last_patient = patients[-1]
    print(f"Last Patient: {last_patient}")
    assert last_patient[1] == "Test Patient", "Patient name mismatch"
    
    print("\nDatabase Test Passed!")

if __name__ == "__main__":
    if os.path.exists('patients.db'):
        os.remove('patients.db') # Clean start
    test_db()
