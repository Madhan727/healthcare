import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'src'))

from analysis import calculate_symptom_score, check_drug_interactions, aggregate_risk

def test_analysis():
    print("Testing Analysis Module...")
    
    # 1. Symptom Score
    symptoms = [
        {"name": "headache", "severity": 3, "duration": 2},
        {"name": "dizziness", "severity": 4, "duration": 1}
    ]
    # Score: 3*(1+0.2) + 4*(1+0.1) = 3.6 + 4.4 = 8.0 / 50 = 0.16
    score = calculate_symptom_score(symptoms)
    print(f"Symptom Score: {score}")
    assert score > 0, "Score should be positive"
    
    # 2. Drug Interactions
    medicines = ["Metformin", "Amlodipine"]
    symptoms_list = [{"name": "dizziness", "severity": 4}]
    alerts = check_drug_interactions(medicines, symptoms_list)
    print(f"Alerts: {alerts}")
    # Expect: Hypoglycemia (Metformin+Dizziness), Side effect (Amlodipine+Dizziness)
    assert len(alerts) > 0, "Should detect interactions"
    
    # 3. Aggregation
    ml_risk = 0.45 # Moderate
    chronic_factors = 1
    result = aggregate_risk(ml_risk, score, chronic_factors, alerts)
    print("\nRisk Report:")
    print(result)
    assert result['risk_percentage'] > 45, "Risk should increase with factors"
    assert result['classification'] in ["Low", "Moderate", "High"], "Invalid classification"
    
    print("\nAnalysis Test Passed!")

if __name__ == "__main__":
    test_analysis()
