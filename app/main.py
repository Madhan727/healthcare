from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from flask_login import login_required, current_user
import json
import os
import sys
from werkzeug.utils import secure_filename

# Import src modules
from src.ocr_engine import extract_text, parse_prescription
from src.drug_intel import normalize_name, fetch_drug_info
from src.cost_analysis import get_medicine_cost
from src.analysis import calculate_symptom_score, check_drug_interactions, aggregate_risk
from src.risk_model import predict_risk
from src.database import get_disease_map
from .models import PatientRecord
from . import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard/index.html', name=current_user.name)

@main.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        # Use absolute path to ensure robustness across environments
        basedir = os.path.abspath(os.path.dirname(__file__))
        upload_folder = os.path.join(basedir, 'static', 'uploads')
        
        # Ensure directory exists just in case
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        try:
            # OCR
            text = extract_text(filepath)
            raw_medicines = parse_prescription(text)
            
            # Enhanced Intelligence
            medicines = []
            inferred_diseases = set()
            disease_map = get_disease_map()
            
            for med in raw_medicines:
                # 1. Normalize Name
                normalized = normalize_name(med['name']) or med['name']
                
                # 2. Fetch Info
                info = fetch_drug_info(normalized)
                
                # 3. Cost Analysis
                cost = get_medicine_cost(normalized)
                
                # 4. Disease Inference
                if normalized in disease_map:
                    inferred_diseases.add(disease_map[normalized])
                
                medicines.append({
                    "name": normalized,
                    "original_name": med['name'],
                    "dosage": med['dosage'],
                    "frequency": med['frequency'],
                    "info": info,
                    "cost": cost
                })
                
            return jsonify({
                'success': True,
                'medicines': medicines,
                'inferred_diseases': list(inferred_diseases),
                'image_path': url_for('static', filename=f'uploads/{filename}') # Return web path
            })
        except Exception as e:
            current_app.logger.error(f"Analysis Failed: {e}")
            return jsonify({'error': str(e)}), 500

@main.route('/analyze_risk', methods=['POST'])
@login_required
def analyze_risk():
    data = request.json
    medicines = data.get('medicines', [])
    symptoms = data.get('symptoms', [])
    
    # Logic similar to before but with enhanced data available
    # Medicines might now be objects with 'name'
    med_names = [m['name'] if isinstance(m, dict) else m for m in medicines]
    
    # 1. ML Risk
    user_features = [60, 1, 0, 140, 240, 0, 1, 150, 0, 1.5, 1, 0, 2] # Mock profile
    ml_risk_prob = predict_risk(user_features)
    
    # 2. Symptom Score
    symptom_score = calculate_symptom_score(symptoms)
    
    # 3. Alerts
    # We can use the info we fetched earlier if passed back, or re-check interactions
    alerts = check_drug_interactions(med_names, symptoms)
    
    # 4. Aggregation
    disease_map = get_disease_map()
    chronic_count = 0
    inferred = set()
    for m in med_names:
        if m in disease_map:
            inferred.add(disease_map[m])
    chronic_count = len(inferred)
    
    # 5. Predictive Symptom Analysis (History Check)
    # Check if user has had same symptoms recently or if symptoms match inferred disease (Validation)
    history_alerts = []
    
    # Check for chronic symptoms (appearing in last 3 records)
    recent_records = PatientRecord.query.filter_by(user_id=current_user.id).order_by(PatientRecord.date_created.desc()).limit(3).all()
    
    current_symptom_names = [s['name'].lower() for s in symptoms]
    
    for s_name in current_symptom_names:
        count = 0
        for record in recent_records:
            if record.symptoms:
                hist_symptoms = json.loads(record.symptoms) 
                # hist_symptoms is list of dicts
                if any(hs['name'].lower() == s_name for hs in hist_symptoms):
                    count += 1
        
        if count >= 2: # Appeared in majority of recent 3 checks
             history_alerts.append(f"Chronic Alert: '{s_name}' has persisted over recent visits.")
             
    # Notification: Match Symptom to Inferred Disease
    # Example: Diabetes (Metaformin) causes "fatigue" or "thirst"
    # We can add a simple map here or use an external one.
    # For demo, hardcode common correlations.
    disease_symptom_map = {
        "Diabetes": ["thirst", "fatigue", "urination", "hunger", "vision"],
        "Hypertension": ["headache", "dizziness", "vision", "chest pain"],
        "Hyperlipidemia": ["chest pain", "faint"]
    }
    
    for disease in inferred:
        possible_symptoms = disease_symptom_map.get(disease, [])
        for ps in possible_symptoms:
            if ps in current_symptom_names: # Fuzzy match ideal, but exact substring ok
                 history_alerts.append(f"Insight: '{ps}' is a common symptom of {disease}. Consult doctor for management.")
                 
    # Add history alerts to final report
    alerts.extend(history_alerts)

    report = aggregate_risk(ml_risk_prob, symptom_score, chronic_count, alerts)
    
    # Save to User's Record
    import json
    new_record = PatientRecord(
        user_id=current_user.id,
        patient_name=current_user.name, # Or separate patient field
        medicines=json.dumps(medicines),
        diseases=json.dumps(list(inferred)),
        symptoms=json.dumps(symptoms), # Save symptoms
        risk_score=report['risk_percentage'],
        risk_class=report['classification']
    )
    db.session.add(new_record)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'report': report,
        'saved_id': new_record.id
    })
