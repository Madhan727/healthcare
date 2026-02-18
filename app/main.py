from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import sys

# Import src modules
# Need to ensure src is in path or import relatively if structure allows
# For this setup, we assume app is run from root, so 'src' is importable
from src.ocr_engine import extract_text, parse_prescription
from src.drug_intel import normalize_name, fetch_drug_info
from src.cost_analysis import get_medicine_cost
from src.analysis import calculate_symptom_score, check_drug_interactions, aggregate_risk
from src.risk_model import predict_risk
from src.database import get_disease_map # We might want to migrate this logic to models or utils
from .models import PatientRecord
from . import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

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
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
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
            'image_path': filepath
        })

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
    
    report = aggregate_risk(ml_risk_prob, symptom_score, chronic_count, alerts)
    
    # Save to User's Record
    import json
    new_record = PatientRecord(
        user_id=current_user.id,
        patient_name=current_user.name, # Or separate patient field
        medicines=json.dumps(medicines),
        diseases=json.dumps(list(inferred)),
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
