import sys
import os
import numpy as np

sys.path.append(os.path.join(os.getcwd(), 'src'))

from risk_model import train_model, predict_risk

def test_risk_model():
    print("Testing Risk Model...")
    
    # Train model (should use synthetic data)
    print("Training Model...")
    train_model()
    
    # Test Prediction
    print("Testing Prediction...")
    # Dummy features (13 features)
    features = [63, 1, 3, 145, 233, 1, 0, 150, 0, 2.3, 0, 0, 1]
    prob = predict_risk(features)
    
    print(f"Predicted Risk Probability: {prob:.4f}")
    assert 0 <= prob <= 1, "Probability out of range"
    
    print("\nRisk Model Test Passed!")

if __name__ == "__main__":
    test_risk_model()
