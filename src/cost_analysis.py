import random

def get_medicine_cost(medicine_name):
    """
    Returns estimated cost and alternatives.
    Since real-time pricing APIs require paid keys (e.g., GoodRx), 
    we simulate this with realistic logic for the demo.
    """
    # Mock Database of costs
    # Format: (Brand Price, Generic Price, Generic Name)
    drug_db = {
        "Metformin": (15.00, 4.00, "Metformin HCL"),
        "Amlodipine": (20.00, 5.00, "Amlodipine Besylate"),
        "Atorvastatin": (25.00, 8.00, "Atorvastatin Calcium"),
        "Lisinopril": (12.00, 3.00, "Lisinopril"),
        "Losartan": (18.00, 6.00, "Losartan Potassium"),
        "Levothyroxine": (22.00, 9.00, "Levothyroxine Sodium"),
        "Omeprazole": (20.00, 7.00, "Omeprazole Magnesium"),
        "Amoxicillin": (10.00, 4.00, "Amoxicillin"),
        "Paracetamol": (5.00, 1.00, "Acetaminophen"),
    }
    
    clean_name = medicine_name.capitalize()
    
    if clean_name in drug_db:
        brand_price, generic_price, generic_name = drug_db[clean_name]
        return {
            "medicine": clean_name,
            "brand_price": brand_price,
            "generic_price": generic_price,
            "generic_name": generic_name,
            "savings": brand_price - generic_price,
            "currency": "$"
        }
    
    # Fallback for unknown drugs
    base_price = round(random.uniform(10, 50), 2)
    return {
        "medicine": clean_name,
        "brand_price": base_price,
        "generic_price": round(base_price * 0.4, 2), # Assume 60% savings
        "generic_name": f"Generic {clean_name}",
        "savings": round(base_price * 0.6, 2),
        "currency": "$"
    }
