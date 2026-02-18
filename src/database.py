import sqlite3
import json
import os

DB_PATH = 'patients.db'
MEDICINES_DATA_PATH = os.path.join('data', 'medicines.json')

def init_db():
    """
    Initializes the SQLite database.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Create table with structured columns
    # medicines: JSON string of list of medicines
    # diseases: JSON string of inferred diseases
    c.execute('''CREATE TABLE IF NOT EXISTS patients
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, 
                  medicines TEXT, 
                  diseases TEXT, 
                  risk_score REAL,
                  consultation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_patient_record(data):
    """
    Saves the patient record to the database.
    data format:
    {
        "name": str,
        "medicines": list,
        "diseases": list,
        "risk_score": float
    }
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO patients (name, medicines, diseases, risk_score) VALUES (?, ?, ?, ?)",
              (data.get('name', 'Unknown'), 
               json.dumps(data.get('medicines', [])), 
               json.dumps(data.get('diseases', [])), 
               data.get('risk_score', 0.0)))
    conn.commit()
    conn.close()

def get_all_patients():
    """
    Retrieves all patient records.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM patients")
    rows = c.fetchall()
    conn.close()
    return rows

def get_disease_map():
    """
    Returns a dictionary mapping medicines to diseases from the JSON file.
    """
    try:
        with open(MEDICINES_DATA_PATH, 'r') as f:
            data = json.load(f)
            # data structure: {"medicines": {"Metformin": {"disease": "Diabetes", ...}, ...}}
            # We want {"Metformin": "Diabetes", ...}
            mapping = {med: info['disease'] for med, info in data.get('medicines', {}).items()}
            return mapping
    except FileNotFoundError:
        print(f"Warning: {MEDICINES_DATA_PATH} not found.")
        return {}
    except json.JSONDecodeError:
        print(f"Warning: Error decoding {MEDICINES_DATA_PATH}.")
        return {}
