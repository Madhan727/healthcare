import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pickle
import os

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'models_data', 'cardio_model.pkl')
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'data', 'heart.csv')

def generate_synthetic_data(n_samples=1000):
    """
    Generates a synthetic heart disease dataset for demonstration.
    Features based on UCI Heart Disease dataset.
    """
    np.random.seed(42)
    data = {
        'age': np.random.randint(29, 78, n_samples),
        'sex': np.random.randint(0, 2, n_samples),
        'cp': np.random.randint(0, 4, n_samples), # Chest Pain Type
        'trestbps': np.random.randint(94, 200, n_samples), # Resting BP
        'chol': np.random.randint(126, 564, n_samples), # Cholesterol
        'fbs': np.random.randint(0, 2, n_samples), # Fasting BS > 120 mg/dl
        'restecg': np.random.randint(0, 3, n_samples),
        'thalach': np.random.randint(71, 202, n_samples), # Max HR
        'exang': np.random.randint(0, 2, n_samples), # Exercise Angina
        'oldpeak': np.random.uniform(0, 6.2, n_samples),
        'slope': np.random.randint(0, 3, n_samples),
        'ca': np.random.randint(0, 4, n_samples),
        'thal': np.random.randint(0, 4, n_samples),
        'target': np.random.randint(0, 2, n_samples)
    }
    return pd.DataFrame(data)

def train_model(data_path=None):
    """
    Trains the Logistic Regression model.
    If data_path is None, uses synthetic data.
    """
    if data_path and os.path.exists(data_path):
        df = pd.read_csv(data_path)
    else:
        print("Using synthetic data for training...")
        df = generate_synthetic_data()
    
    X = df.drop('target', axis=1)
    y = df['target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {accuracy:.2f}")
    
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model saved to {MODEL_PATH}")

def predict_risk(features):
    """
    Predicts the cardiovascular risk probability.
    features: list or array of shape (1, n_features)
    """
    if not os.path.exists(MODEL_PATH):
        print("Model not found. Training new model...")
        train_model()
        
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
        
    # Ensure features is 2D
    features_arr = np.array(features).reshape(1, -1)
    
    # Get probability of class 1 (Heart Disease)
    prob = model.predict_proba(features_arr)[0][1]
    return prob
