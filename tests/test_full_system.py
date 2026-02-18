import sys
import os
import unittest
from flask_testing import TestCase

# Add root path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import User
from src.drug_intel import fetch_drug_info, normalize_name
from src.cost_analysis import get_medicine_cost

class HealthAppTests(TestCase):
    def create_app(self):
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # In-memory DB
        app.config['WTF_CSRF_ENABLED'] = False
        return app

    def setUp(self):
        db.create_all()
        # Create user
        user = User(email='test@example.com', name='Test User', password='scrypt:32768:8:1$Salt$Hash') # Mock hash
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_authentication(self):
        # Register
        res = self.client.post('/register', data={
            'email': 'new@test.com', 'name': 'New User', 'password': 'password'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Log In', res.data)
        
        # Login
        # Note: Proper login test needs real hash logic or full flow, 
        # but here we test the route existence and redirect.
        res = self.client.get('/login')
        self.assertEqual(res.status_code, 200)

    def test_drug_intel(self):
        # Fuzzy Match
        self.assertEqual(normalize_name("Metforrrmin"), "Metformin")
        
        # OpenFDA (Mock or Real if net valid)
        # We assume net is valid or it handles gracefully
        info = fetch_drug_info("Metformin")
        self.assertNotEqual(info['generic_name'], "Unknown")

    def test_cost_analysis(self):
        cost = get_medicine_cost("Metformin")
        self.assertIn('savings', cost)
        self.assertTrue(cost['brand_price'] > cost['generic_price'])

if __name__ == '__main__':
    unittest.main()
