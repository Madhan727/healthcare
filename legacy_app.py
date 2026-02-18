import os
import sys
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from ocr_engine import extract_text, parse_prescription
from database import init_db, save_patient_record, get_disease_map
from risk_model import predict_risk
from analysis import calculate_symptom_score, check_drug_interactions, aggregate_risk

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize DB on start
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/report')
def report():
    return render_template('result.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # OCR Processing
        try:
            text = extract_text(filepath)
            medicines = parse_prescription(text)
            
            # Infer diseases for context
            disease_map = get_disease_map()
            inferred_diseases = []
            for med in medicines:
                match = next((m for m in disease_map if m.lower() == med['name'].lower()), None)
                if match:
                    disease = disease_map[match]
                    if disease not in inferred_diseases:
                        inferred_diseases.append(disease)
            
            return jsonify({
                'success': True,
                'medicines': medicines,
                'inferred_diseases': inferred_diseases,
                'image_path': filepath
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze_risk():
    data = request.json
    medicines = data.get('medicines', [])
    symptoms = data.get('symptoms', [])
    
    # Calculate Risk
    # 1. ML Risk (using default profile + potentially age/gender if we had inputs)
    # For now using a standard profile simulation
    user_features = [60, 1, 0, 140, 240, 0, 1, 150, 0, 1.5, 1, 0, 2]
    ml_risk_prob = predict_risk(user_features)
    
    # 2. Symptom Score
    symptom_score = calculate_symptom_score(symptoms)
    
    # 3. Alerts
    alerts = check_drug_interactions(medicines, symptoms)
    
    # 4. Aggregation
    # Convert medicines dict list to simple names list for aggregation if needed
    # But aggregate_risk expects "chronic_factors_count"
    
    disease_map = get_disease_map()
    inferred_diseases = []
    for med in medicines:
        name = med['name']
        match = next((m for m in disease_map if m.lower() == name.lower()), None)
        if match:
             if disease_map[match] not in inferred_diseases:
                 inferred_diseases.append(disease_map[match])
                 
    report = aggregate_risk(ml_risk_prob, symptom_score, len(inferred_diseases), alerts)
    
    # Save to DB
    save_patient_record({
        "name": "Web User", # Placeholder
        "medicines": [m['name'] for m in medicines],
        "diseases": inferred_diseases,
        "risk_score": report['risk_percentage']
    })
    
    return jsonify({
        'success': True,
        'report': report,
        'inferred_diseases': inferred_diseases
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    from database import get_all_patients
    # Get last 10 records
    data = get_all_patients()
    # Data is list of tuples, need to convert to dicts
    # (id, name, medicines, diseases, risk_score, date)
    history = []
    for row in reversed(data[-10:]):
        history.append({
            "id": row[0],
            "name": row[1],
            "risk_score": row[4],
            "date": row[5]
        })
    return jsonify(history)

@app.route('/api/analyze_realtime', methods=['POST'])
def analyze_realtime():
    data = request.json
    medicines = data.get('medicines', [])
    symptoms = data.get('symptoms', [])
    
    # Calculate Risk (Simulated for realtime feedback)
    user_features = [60, 1, 0, 140, 240, 0, 1, 150, 0, 1.5, 1, 0, 2]
    ml_risk_prob = predict_risk(user_features)
    symptom_score = calculate_symptom_score(symptoms)
    processed_meds = [{"name": m} for m in medicines] if isinstance(medicines[0], str) else medicines
    alerts = check_drug_interactions(processed_meds, symptoms)
    
    disease_map = get_disease_map()
    inferred_diseases = []
    for med in medicines:
        name = med['name'] if isinstance(med, dict) else med
        match = next((m for m in disease_map if m.lower() == name.lower()), None)
        if match:
             if disease_map[match] not in inferred_diseases:
                 inferred_diseases.append(disease_map[match])
                 
    report = aggregate_risk(ml_risk_prob, symptom_score, len(inferred_diseases), alerts)
    
    return jsonify({
        'success': True,
        'risk_percentage': report['risk_percentage'],
        'classification': report['classification'],
        'recommendation': report['recommendation'],
        'alerts': alerts
    })

if __name__ == '__main__':
    app.run(debug=True)
