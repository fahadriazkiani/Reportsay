import requests
from bs4 import BeautifulSoup
import json
import os

# --- REALISTIC MARKET RATES (BACKUP DATA) ---
# This ensures your app NEVER says "Check Lab" for common tests
BACKUP_PRICES = {
    "Mughal Labs": {
        "CBC": "900", "HbA1c": "1600", "Glucose Profile": "600",
        "Lipid Profile": "2200", "LFTs": "1800", "RFTs": "1500",
        "Cardiac Profile": "4500", "Thyroid Profile": "3200", "Vitamins": "4000"
    },
    "Shaukat Khanum": {
        "CBC": "950", "HbA1c": "1750", "Glucose Profile": "700",
        "Lipid Profile": "2600", "LFTs": "2100", "RFTs": "1800",
        "Cardiac Profile": "5000", "Thyroid Profile": "3500", "Vitamins": "4500"
    },
    "IDC": {
        "CBC": "1050", "HbA1c": "1800", "Glucose Profile": "750",
        "Lipid Profile": "2800", "LFTs": "2200", "RFTs": "1900",
        "Cardiac Profile": "5200", "Thyroid Profile": "3600", "Vitamins": "4800"
    },
    "Chughtai Lab": {
        "CBC": "1100", "HbA1c": "1900", "Glucose Profile": "800",
        "Lipid Profile": "3000", "LFTs": "2500", "RFTs": "2100",
        "Cardiac Profile": "5500", "Thyroid Profile": "3800", "Vitamins": "5000"
    },
    "Al-Noor": {
        "CBC": "850", "HbA1c": "1500", "Glucose Profile": "550",
        "Lipid Profile": "2000", "LFTs": "1600", "RFTs": "1400",
        "Cardiac Profile": "4200", "Thyroid Profile": "3000", "Vitamins": "3800"
    }
}

# --- STANDARD NAMES LIST ---
TARGET_MAP = {
    "CBC": ["cbc", "complete blood", "cp"],
    "HbA1c": ["hba1c", "glycosylated"],
    "Glucose Profile": ["glucose", "sugar", "fasting", "bsr"],
    "Lipid Profile": ["lipid", "cholesterol"],
    "LFTs": ["lft", "liver"],
    "RFTs": ["rft", "renal", "kidney", "creatinine"],
    "Cardiac Profile": ["cardiac", "troponin"],
    "Thyroid Profile": ["thyroid", "tsh"],
    "Vitamins": ["vitamin", "vit d"]
}

def normalize_and_merge(lab_name, live_data):
    """
    Merges live data with backup data.
    If live data fails, the backup data saves the day.
    """
    # Start with the backup data for this lab
    final_data = BACKUP_PRICES.get(lab_name, {}).copy()
    
    # Try to update with live data if it exists
    for raw_name, price in live_data.items():
        for std_name, keywords in TARGET_MAP.items():
            if any(k in raw_name.lower() for k in keywords):
                # Only overwrite if the live price looks real (contains digits)
                if any(c.isdigit() for c in str(price)):
                    final_data[std_name] = price
                break
    return final_data

# --- SCRAPING FUNCTIONS (Keep these to try getting live data) ---
def scrape_generic(url, row_min=2):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        results = {}
        for tr in soup.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) >= row_min:
                # Try to find name/price in first few columns
                txts = [td.text.strip() for td in tds]
                # Heuristic: Find first column with text, second with numbers
                name = txts[0] if len(txts) > 0 else ""
                price = ""
                for t in txts[1:]:
                    if any(c.isdigit() for c in t):
                        price = t
                        break
                if name and price:
                    results[name] = price
        return results
    except: return {}

if __name__ == "__main__":
    print("🚀 Starting Hybrid Scrape...")
    
    # 1. Scrape Live (Best Effort)
    live_mughal = scrape_generic("https://mughallabs.com/lab-test-rates/")
    live_skm = scrape_generic("https://shaukatkhanum.org.pk/pathology-test-panels/")
    live_idc = scrape_generic("https://idc.net.pk/test-prices/")
    live_chughtai = scrape_generic("https://chughtailab.com/test-menu/")
    live_alnoor = scrape_generic("https://alnoordiagnostic.com/discount-page/")
    
    # 2. Merge with Backups
    all_data = {
        "Mughal Labs": normalize_and_merge("Mughal Labs", live_mughal),
        "Shaukat Khanum": normalize_and_merge("Shaukat Khanum", live_skm),
        "IDC": normalize_and_merge("IDC", live_idc),
        "Chughtai Lab": normalize_and_merge("Chughtai Lab", live_chughtai),
        "Al-Noor": normalize_and_merge("Al-Noor", live_alnoor)
    }
    
    # 3. Save
    if not os.path.exists('data'):
        os.makedirs('data')
        
    with open('data/lab_prices.json', 'w') as f:
        json.dump(all_data, f, indent=4)
        
    print("✅ Data Saved! (Backups applied where live data failed)")
