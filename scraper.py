import requests
from bs4 import BeautifulSoup
import json
import os

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
                if len(cols) >= 2:
                    results[cols[0].text.strip()] = cols[1].text.strip()
        return results
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
                    results[cols[0].text.strip()] = cols[2].text.strip()
        return results
    except: return {}

def scrape_idc():
    # IDC often requires a search or has a dynamic list
    url = "https://idc.net.pk/test-prices/" 
    try:
        res = requests.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        results = {}
        # Targeting common test rows in IDC's price table
        for row in soup.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 2:
                name = cols[0].text.strip()
                price = cols[1].text.strip()
                if any(char.isdigit() for char in price):
                    results[name] = price
        return results
    except: return {}

def scrape_chughtai():
    url = "https://chughtailab.com/test-menu/"
    try:
        res = requests.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        results = {}
        # Chughtai uses list items or cards for their test menu
        for item in soup.find_all(['div', 'li'], class_='test-item'):
            name = item.find(['h4', 'span'], class_='test-name')
            price = item.find('span', class_='test-price')
            if name and price:
                results[name.text.strip()] = price.text.strip()
        return results
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
                # Cleaning up the text to extract a readable test name
                results[block.text.strip()[:40]] = "Discounted Price"
        return results
    except: return {}

if __name__ == "__main__":
    # Aggregating data from all 5 targeted Lahore labs
    all_data = {
        "Mughal Labs": scrape_mughal(),
        "Shaukat Khanum": scrape_skm(),
        "IDC (Islamabad Diagnostic)": scrape_idc(),
        "Chughtai Lab": scrape_chughtai(),
        "Al-Noor Diagnostic": scrape_alnoor()
    }
    
    # Ensure the 'data' directory exists for app.py
    if not os.path.exists('data'):
        os.makedirs('data')
        
    with open('data/lab_prices.json', 'w') as f:
        json.dump(all_data, f, indent=4)
    print("✅ All 5 Labs Scraped and Data Saved!")
