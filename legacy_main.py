import os
import sys
import json
import warnings
warnings.filterwarnings('ignore') # Suppress warnings

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from ocr_engine import extract_text, parse_prescription
from database import init_db, save_patient_record, get_disease_map
from risk_model import predict_risk, train_model
from analysis import calculate_symptom_score, check_drug_interactions, aggregate_risk

def main():
    print("================================================================")
    print("   AI-Powered Multi-Disease Prescription Intelligence & Risk Analysis")
    print("================================================================")
    
    # Initialize DB
    init_db()
    disease_map = get_disease_map()
    
    # 1. Image Input
    image_path = input("\nEnter Prescription Image Path (or type 'TEST' for demo): ").strip()
    
    extracted_text = ""
    if image_path.upper() == 'TEST':
        print("\n[INFO] Using Test Data...")
        extracted_text = "Dr. Smith. Rx: Metformin 500mg OD. Amlodipine 5mg 1-0-1. Atorvastatin 20mg Once a day."
        print(f"Simulated Extracted Text: {extracted_text}")
    elif os.path.exists(image_path):
        print("\n[INFO] Processing Image...")
        extracted_text = extract_text(image_path)
        print(f"Extracted Text: {extracted_text[:100]}...")
    else:
        print("[ERROR] File not found. Exiting.")
        return

    # 2. Extract Medicines
    print("\n[INFO] Parsing Medicines...")
    medicines = parse_prescription(extracted_text)
    if not medicines:
        print("[WARN] No medicines found. Please check image quality or format.")
    else:
        print("Detected Medicines:")
        for med in medicines:
            print(f" - {med['name']} ({med['dosage']}, {med['frequency']})")

    # 3. Infer Diseases
    print("\n[INFO] Inferring Chronic Conditions...")
    inferred_diseases = []
    for med in medicines:
        med_name = med['name']
        # Simple lookup in our map
        # Check matching keys
        match = next((m for m in disease_map if m.lower() == med_name.lower()), None)
        if match:
            disease = disease_map[match]
            if disease not in inferred_diseases:
                inferred_diseases.append(disease)
    
    print(f"Inferred Conditions: {', '.join(inferred_diseases) if inferred_diseases else 'None'}")
    
    # 4. Symptom Input
    print("\nEnter Symptoms (comma separated, e.g., headache, dizziness):")
    symptoms_input = input("> ").strip().split(',')
    symptoms = []
    for s_name in symptoms_input:
        s_name = s_name.strip()
        if s_name:
            print(f"Severity for '{s_name}' (1-10): ", end='')
            try:
                sev = int(input() or 5)
            except:
                sev = 5
            print(f"Duration for '{s_name}' (days): ", end='')
            try:
                dur = int(input() or 1)
            except:
                dur = 1
            symptoms.append({"name": s_name, "severity": sev, "duration": dur})
            
    # 5. Risk Analysis
    print("\n[INFO] Calculating Risk...")
    
    # ML Prediction (Mock features for demo)
    # In real app, we would ask for age, bp, chol, etc.
    # Here we simulate valid features
    user_features = [60, 1, 0, 140, 240, 0, 1, 150, 0, 1.5, 1, 0, 2] # Default average-risk profile
    ml_risk_prob = predict_risk(user_features)
    
    # Symptom Score
    symptom_score = calculate_symptom_score(symptoms)
    
    # Alerts
    alerts = check_drug_interactions(medicines, symptoms)
    
    # Aggregation
    report = aggregate_risk(ml_risk_prob, symptom_score, len(inferred_diseases), alerts)
    
    # 6. Output
    print("\n================================================================")
    print("                    FINAL RISK REPORT")
    print("================================================================")
    print(f"Patient Name: Demo User") # Placeholder
    print(f"Risk Classification: {report['classification'].upper()}")
    print(f"Risk Percentage: {report['risk_percentage']}%")
    print(f"Recommendation: {report['recommendation']}")
    print("\nDetailed Reasoning:")
    for reason in report['reasoning']:
        print(f" - {reason}")
    print("================================================================")
    
    # Save Record
    save_patient_record({
        "name": "Demo User",
        "medicines": [m['name'] for m in medicines],
        "diseases": inferred_diseases,
        "risk_score": report['risk_percentage']
    })
    print("\n[INFO] Record saved to database.")

if __name__ == "__main__":
    main()
