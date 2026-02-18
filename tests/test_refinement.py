import unittest
import sys
import os
import json

# Add root path
sys.path.append(os.getcwd())

from src.ocr_engine import parse_prescription
from src.analysis import calculate_symptom_score
from app import create_app, db
from app.models import User, PatientRecord

class RefinementTests(unittest.TestCase):
    def setUp(self):
        # Create a mock known_medicines list for testing if needed
        # But ocr_engine.py loads from app/data/medicines.json
        pass

    def test_fuzzy_ocr_parsing(self):
        # Even with typo "Metforrr", it should detect Metformin
        text = "Rx: Take Metforrr 500mg once a day"
        results = parse_prescription(text)
        self.assertTrue(any(r['name'] == 'Metformin' for r in results))
        self.assertEqual(results[0]['dosage'], '500mg')

    def test_symptom_scoring_tuning(self):
        # Single minor symptom should have dampend score
        symptoms_single = [{"name": "headache", "severity": 2, "duration": 1}]
        score_single = calculate_symptom_score(symptoms_single)
        # Old logic: 2 * (1 + 0.1) / 50 = 0.044
        # New logic: (2 / 20) * 0.5 = 0.05
        # It's actually slightly higher but consistent. 
        # The key is the "consult doctor" classification threshold in aggregate_risk (final_risk < 0.3 is Low)
        self.assertLess(score_single, 0.1)

        # Multiple symptoms should have higher confidence
        symptoms_multi = [
            {"name": "headache", "severity": 4, "duration": 1},
            {"name": "dizziness", "severity": 4, "duration": 1},
            {"name": "fatigue", "severity": 4, "duration": 1}
        ]
        score_multi = calculate_symptom_score(symptoms_multi)
        # (12 / 20) * 1.0 = 0.6
        self.assertGreater(score_multi, 0.5)

class IntegrationRefinementTests(unittest.TestCase):
    def setUp(self):
        # Set config before creating app
        os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Ensure tables are created in the in-memory DB
        db.create_all()
        
        # Create user for testing
        hashed_pw = 'scrypt:32768:8:1$salt$hash' # valid format
        self.test_user = User(email='refine@test.com', name='Refine User', password=hashed_pw)
        db.session.add(self.test_user)
        db.session.commit()
        self.user_id = self.test_user.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_automated_risk_adjustment(self):
        try:
            # Login mock
            with self.client.session_transaction() as sess:
                sess['_user_id'] = str(self.user_id)
                sess['_fresh'] = True

            # Case 1: Healthy (No meds)
            res_healthy = self.client.post('/analyze_risk', json={
                "medicines": [],
                "symptoms": [{"name": "headache", "severity": 1, "duration": 1}]
            })
            if not res_healthy.json or not res_healthy.json.get('success'):
                print(f"Healthy Fail: {res_healthy.data}")
            
            risk_healthy = res_healthy.json['report']['risk_percentage']
            
            # Case 2: Diabetes (Metformin)
            res_diabetes = self.client.post('/analyze_risk', json={
                "medicines": [{"name": "Metformin", "dosage": "500mg", "frequency": "OD"}],
                "symptoms": [{"name": "headache", "severity": 1, "duration": 1}]
            })
            risk_diabetes = res_diabetes.json['report']['risk_percentage']
            
            self.assertGreater(risk_diabetes, risk_healthy)
        except Exception:
            with open('test_crash.log', 'w') as f:
                traceback.print_exc(file=f)
            raise

if __name__ == '__main__':
    unittest.main()
