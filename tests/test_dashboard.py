import sys
import os
import json

# Add root path
sys.path.append(os.getcwd())

from app import app, init_db, save_patient_record

def test_dashboard_apis():
    print("Testing Enhanced Dashboard APIs...")
    client = app.test_client()
    init_db()
    
    # 1. Test History (Empty)
    res = client.get('/api/history')
    assert res.status_code == 200
    assert isinstance(res.json, list)
    print("GET /api/history (Empty) passed")
    
    # 2. Add Dummy Record
    save_patient_record({
        "name": "History Test",
        "medicines": ["Metformin"],
        "diseases": ["Diabetes"],
        "risk_score": 15.5
    })
    
    # 3. Test History (Populated)
    res = client.get('/api/history')
    data = res.json
    assert len(data) > 0
    assert data[0]['name'] == 'History Test'
    print("GET /api/history (Populated) passed")
    
    # 4. Test Realtime Analysis
    payload = {
        "medicines": [{"name": "Metformin", "dosage": "500mg", "frequency": "OD"}],
        "symptoms": [{"name": "dizziness", "severity": 8, "duration": 1}]
    }
    res = client.post('/api/analyze_realtime', json=payload)
    assert res.status_code == 200
    data = res.json
    assert data['success'] == True
    assert data['risk_percentage'] > 0
    assert len(data['alerts']) > 0 # Should flag hypoglycemia interaction
    print("POST /api/analyze_realtime passed")
    
    print("\nEnhanced Platform Verified!")

if __name__ == "__main__":
    test_dashboard_apis()
