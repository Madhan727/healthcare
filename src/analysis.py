def calculate_symptom_score(symptoms):
    """
    Calculates a score based on symptom severity and duration.
    symptoms: list of dicts [{"name": "headache", "severity": 1-5, "duration": 3}]
    """
    score = 0
    for s in symptoms:
        score += s.get('severity', 0) * (1 + (s.get('duration', 0) / 10)) # simple duration weight
    return min(score / 50.0, 1.0) # Normalize to 0-1 (assuming max cumulative severity is rare)

def check_drug_interactions(medicines, symptoms):
    """
    Checks for potential drug interactions or conflicts based on medicine type and symptoms.
    medicines: list of medicine names or dicts
    symptoms: list of symptom names
    """
    alerts = []
    
    # Simple logic based on medicine types
    # Assume we have medicine types available (in a real app, query DB)
    # Here we simulate types based on names
    
    med_names = [m['name'] if isinstance(m, dict) else m for m in medicines]
    symptom_names = [s['name'].lower() for s in symptoms]
    
    for med in med_names:
        med_lower = med.lower()
        if "metformin" in med_lower and ("dizziness" in symptom_names or "shaking" in symptom_names):
            alerts.append(f"Possible Hypoglycemia (Low Sugar) with {med}.")
        if "amlodipine" in med_lower and ("swelling" in symptom_names or "dizziness" in symptom_names):
            alerts.append(f"Possible side effect of {med}: Swelling or Dizziness.")
        if "atorvastatin" in med_lower and "muscle pain" in symptom_names:
            alerts.append(f"Possible Statin-induced muscle pain with {med}.")
            
    # Health Parameter Approximation
    if any("metformin" in m.lower() for m in med_names) and "blurry vision" in symptom_names:
         alerts.append("Flag: Possible uncontrolled glucose levels.")
         
    if any("amlodipine" in m.lower() or "lisinopril" in m.lower() for m in med_names) and "headache" in symptom_names:
         alerts.append("Flag: Possible BP fluctuation.")
         
    return alerts

def aggregate_risk(ml_risk, symptom_score, chronic_factors_count, alerts):
    """
    Combines different risk factors into a final risk assessment.
    """
    # Weighted sum
    # ML Risk (Cardio) has high weight if we are focusing on heart
    # Symptom score adds to urgency
    # Chronic factors amplify base risk
    
    base_risk = ml_risk
    
    # Amplifier
    amplified_risk = base_risk * (1 + (chronic_factors_count * 0.1))
    
    # Add symptom impact
    total_risk = amplified_risk + (symptom_score * 0.3)
    
    # Cap at 1.0 (100%)
    final_risk = min(total_risk, 0.99)
    
    # Classification
    if final_risk < 0.3:
        classification = "Low"
        rec = "Continue with prescribed medication. Monitor regularly."
    elif final_risk < 0.7:
        classification = "Moderate"
        rec = "Consult Doctor. Monitor symptoms closely."
    else:
        classification = "High"
        rec = "Urgent: Consult Doctor immediately or visit ER."
        
    reasoning = []
    reasoning.append(f"Base Cardiovascular Risk: {base_risk:.1%}")
    reasoning.append(f"Symptom Impact: +{symptom_score:.1%}")
    reasoning.append(f"Chronic Disease Factor: +{chronic_factors_count * 10}%")
    reasoning.extend(alerts)
    
    return {
        "risk_percentage": round(final_risk * 100, 2),
        "classification": classification,
        "recommendation": rec,
        "reasoning": reasoning
    }
