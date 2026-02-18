import sys
import os
import unittest
import json
from flask_testing import TestCase

# Add root path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import User

class PredictiveAnalysisTests(TestCase):
    def create_app(self):
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # In-memory DB
        app.config['WTF_CSRF_ENABLED'] = False
        return app

    def setUp(self):
        db.create_all()
        # Create user
        user = User(email='test@example.com', name='Test User', password='scrypt:32768:8:1$Salt$Hash')
        db.session.add(user)
        db.session.commit()
        
        # Login
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_chronic_symptom_alert(self):
        # 1. First Submission (Headache)
        payload = {
            "medicines": [{"name": "Lisinopril"}],
            "symptoms": [{"name": "Headache", "severity": 5, "duration": 1}]
        }
        res1 = self.client.post('/analyze_risk', json=payload)
        data1 = res1.json
        self.assertTrue(data1['success'])
        
        alerts1 = data1['report'].get('reasoning', [])
        # Should not have chronic alert yet (only 1 occurrence)
        self.assertFalse(any("Chronic Alert" in a for a in alerts1))
        
        # 2. Second Submission (Headache again)
        res2 = self.client.post('/analyze_risk', json=payload)
        # Should have persisted? Count >= 2 in recent 3 checks.
        # Yes, logic was: count in recent records (which includes the one just saved? No, usually fetched before saving current)
        # Ah, in main.py: 
        #   recent_records = PatientRecord.query...limit(3).all()
        #   Then calculate report.
        #   Then save NEW record.
        # So for 2nd submission, recent_records has 1 record with "Headache".
        # Current symptoms has "Headache".
        # Logic: if count >= 2. Here count=1. So no alert on 2nd submission IF threshold is >= 2.
        # My logic was `if count >= 2`.
        # So 2nd submission sees 1 prior record. 3rd submission sees 2 prior records.
        
        # 3. Third Submission (Headache again)
        res3 = self.client.post('/analyze_risk', json=payload)
        data3 = res3.json
        alerts3 = data3['report'].get('reasoning', [])
        
        # Now recent records has 2 entries. Count = 2.
        # So we expect alert.
        found_chronic = any("Chronic Alert" in a for a in alerts3)
        self.assertTrue(found_chronic, "Should detect chronic symptom alert on 3rd visit")

    def test_disease_symptom_correlation(self):
        # Diabetes (Metformin) and Thirst
        payload = {
            "medicines": [{"name": "Metformin"}],
            "symptoms": [{"name": "thirst", "severity": 5, "duration": 1}]
        }
        res = self.client.post('/analyze_risk', json=payload)
        data = res.json
        alerts = data['report'].get('reasoning', [])
        
        # Expect insight
        found_insight = any("Insight: 'thirst' is a common symptom of Diabetes" in a for a in alerts)
        self.assertTrue(found_insight, "Should detect symptom correlation with inferred disease")

if __name__ == '__main__':
    unittest.main()
