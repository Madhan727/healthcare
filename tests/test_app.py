import sys
import os
import json
import io

# Add root path
sys.path.append(os.getcwd())

from app import app

def test_routes():
    print("Testing Flask Routes...")
    client = app.test_client()
    
    # 1. Home
    response = client.get('/')
    assert response.status_code == 200
    print("GET / passed")
    
    # 2. Symptoms Page (Render check)
    response = client.get('/symptoms')
    assert response.status_code == 200
    print("GET /symptoms passed")
    
    # 3. Analyze API
    payload = {
        "medicines": [{"name": "Metformin", "dosage": "500mg", "frequency": "OD"}],
        "symptoms": [{"name": "dizziness", "severity": 5, "duration": 1}]
    }
    response = client.post('/analyze', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'report' in data
    print("POST /analyze passed")
    
    print("\nWeb App Routes Verified!")

if __name__ == "__main__":
    test_routes()
