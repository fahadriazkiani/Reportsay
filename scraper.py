import requests
from bs4 import BeautifulSoup
import json
import os

# --- STANDARD LIST YOU REQUESTED ---
TARGET_TESTS = {
    "CBC": ["cbc", "complete blood count", "blood cp", "c.b.c"],
    "HbA1c": ["hba1c", "glycosylated", "hemoglobin a1c"],
    "Glucose Profile": ["glucose", "sugar", "bsr", "bsf", "fasting"],
    "Lipid Profile": ["lipid", "cholesterol", "triglycerides"],
    "LFTs": ["lft", "liver function", "bilirubin", "sgpt", "sgot"],
    "RFTs": ["rft", "renal", "kidney", "urea", "creatinine"],
    "Cardiac Profile": ["cardiac", "troponin", "ck-mb"],
    "Thyroid Profile": ["thyroid", "tsh", "t3", "t4"],
    "Vitamins": ["vitamin", "vit d", "vit b12"]
}

def normalize_keys(raw_data):
    """
    Scans the messy raw data and creates clean, standard keys 
    (e.g., turns 'C.B.C (Complete Blood)' into 'CBC').
    """
    clean_data = {}
    
    # 1. Copy raw data first (so we don't lose anything)
    clean_data = raw_data.copy()
    
    # 2. Add Standard Keys if found
    for standard_name, keywords in TARGET_TESTS.items():
        # Look for a match in the raw data
        found_price = None
        for raw_name, price in raw_data.items():
            # Check if any keyword exists in the raw name
            if any(k in raw_name.lower() for k in keywords):
                found_price = price
                break # Stop after finding the first best match
        
        # If we found a price, add it under the Standard Name
        if found_price:
            clean_data[standard_name] = found_price
            
    return clean_data

# --- LAB SCRAPERS ---
def scrape_mughal():
    url = "https://mughallabs.com/lab-test-rates/"
    try:
        res = requests.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        results = {}
        table = soup.find('table')
        if table:
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) >= 3: 
                    name = cols[1].text.strip()
                    price = cols[2].text.strip()
                    results[name] = price
        return normalize_keys(results) # <--- Clean the data
    except: return {}

def scrape_skm():
    url = "https://shaukatkhanum.org.pk/pathology-test-panels/"
    try:
        res = requests.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        results = {}
        table = soup.find('table')
        if table:
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    name = cols[1].text.strip()
                    price = cols[2].text.strip()
                    results[name] = price
        return normalize_keys(results)
    except: return {}

def scrape_idc():
    url = "https://idc.net.pk/test-prices/" 
    try:
        res = requests.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        results = {}
        for row in soup.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 2:
                name = cols[0].text.strip()
                price = cols[1].text.strip()
                if any(char.isdigit() for char in price):
                    results[name] = price
        return normalize_keys(results)
    except: return {}

def scrape_chughtai():
    url = "https://chughtailab.com/test-menu/"
    try:
        res = requests.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        results = {}
        for item in soup.find_all(['div', 'li'], class_='test-item'):
            name = item.find(['h4', 'span'], class_='test-name')
            price = item.find('span', class_='test-price')
            if name and price:
                results[name.text.strip()] = price.text.strip()
        return normalize_keys(results)
    except: return {}

def scrape_alnoor():
    url = "https://alnoordiagnostic.com/discount-page/"
    try:
        res = requests.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        results = {}
        for block in soup.find_all(['div', 'h3', 'p']):
            text = block.text.lower()
            if "rs." in text:
                clean_name = block.text.strip().split("Rs.")[0].strip()
                results[clean_name[:40]] = "View Discount"
        return normalize_keys(results)
    except: return {}

if __name__ == "__main__":
    all_data = {
        "Mughal Labs": scrape_mughal(),
        "Shaukat Khanum": scrape_skm(),
        "IDC": scrape_idc(),
        "Chughtai Lab": scrape_chughtai(),
        "Al-Noor": scrape_alnoor()
    }
    
    if not os.path.exists('data'):
        os.makedirs('data')
        
    with open('data/lab_prices.json', 'w') as f:
        json.dump(all_data, f, indent=4)
    print("✅ Scrape Complete - Standard Lists Updated!")
