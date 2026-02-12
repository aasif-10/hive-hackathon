"""
H.I.V.E. Intelligence Extractor
Extract scammer intelligence using regex patterns
"""
import re

# Known UPI handles for filtering
KNOWN_UPI_HANDLES = [
    "okhdfc", "okhdfcbank", "okaxis", "oksbi", "paytm",
    "ybl", "ibl", "upi", "gpay", "apl", "waicici",
    "pingpay", "icici", "axl", "indianbank", "okicici"
]

def extract_upi_ids(text: str) -> list:
    """Extract UPI IDs from text"""
    # Pattern for email-like UPI format
    pattern = r'\b[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+\b'
    matches = re.findall(pattern, text.lower())
    
    # Filter to keep only UPI-like IDs
    upi_ids = []
    for match in matches:
        domain = match.split('@')[1]
        # Check if domain matches known UPI handles
        if any(handle in domain for handle in KNOWN_UPI_HANDLES):
            upi_ids.append(match)
        # Or if domain has no dots and is short (likely UPI)
        elif '.' not in domain and len(domain) < 15:
            upi_ids.append(match)
    
    return list(set(upi_ids))  # Remove duplicates

def extract_phone_numbers(text: str) -> list:
    """Extract Indian phone numbers from text"""
    phone_numbers = []
    
    # Pattern 1: +91 format
    pattern1 = r'\+91[-\s]?\d{10}'
    matches1 = re.findall(pattern1, text)
    
    # Pattern 2: 91 prefix format
    pattern2 = r'\b91\d{10}\b'
    matches2 = re.findall(pattern2, text)
    
    # Pattern 3: 10-digit starting with 6-9
    pattern3 = r'\b[6-9]\d{9}\b'
    matches3 = re.findall(pattern3, text)
    
    # Combine and clean
    all_matches = matches1 + matches2 + matches3
    for match in all_matches:
        # Remove dashes and spaces
        cleaned = match.replace('-', '').replace(' ', '')
        phone_numbers.append(cleaned)
    
    return list(set(phone_numbers))  # Remove duplicates

def extract_bank_accounts(text: str) -> list:
    """Extract bank account numbers from text"""
    accounts = []
    
    # Pattern 1: Contextual (with keywords)
    pattern1 = r'(?:account|a/c|ac|acct|savings|current)[\s:.-]*(\d{9,18})'
    matches1 = re.findall(pattern1, text.lower())
    
    # Pattern 2: Standalone long numbers
    pattern2 = r'\b(\d{11,18})\b'
    matches2 = re.findall(pattern2, text)
    
    # Combine both
    accounts = list(set(matches1 + matches2))
    
    return accounts

def extract_phishing_links(text: str) -> list:
    """Extract phishing and suspicious links from text"""
    links = []
    
    # Pattern 1: Standard URLs
    pattern1 = r'https?://[^\s<>"{}|\\^`\[\]]+'
    matches1 = re.findall(pattern1, text)
    
    # Pattern 2: Short URLs
    pattern2 = r'\b(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|ow\.ly)/[^\s]+'
    matches2 = re.findall(pattern2, text.lower())
    
    # Pattern 3: Suspicious domains
    pattern3 = r'\b(?:www\.)?[a-zA-Z0-9-]+(?:bank|sbi|hdfc|icici|verify|kyc|update)[a-zA-Z0-9-]*\.[a-zA-Z]{2,}\b'
    matches3 = re.findall(pattern3, text.lower())
    
    # Combine all
    links = list(set(matches1 + matches2 + matches3))
    
    return links

def extract_suspicious_keywords(text: str) -> list:
    """Extract suspicious keywords found in text"""
    keywords_to_check = [
        "urgent", "immediately", "verify", "blocked", "suspended",
        "otp", "pin", "password", "download", "click here",
        "kyc", "legal action", "arrested", "penalty", "account number"
    ]
    
    text_lower = text.lower()
    found = [kw for kw in keywords_to_check if kw in text_lower]
    
    return found

def extract_all_intelligence(text: str) -> dict:
    """Extract all intelligence from a message"""
    return {
        "upiIds": extract_upi_ids(text),
        "phoneNumbers": extract_phone_numbers(text),
        "bankAccounts": extract_bank_accounts(text),
        "phishingLinks": extract_phishing_links(text),
        "suspiciousKeywords": extract_suspicious_keywords(text)
    }

def merge_intelligence(existing: dict, new: dict) -> dict:
    """Merge new intelligence with existing intelligence"""
    merged = {}
    
    for key in existing.keys():
        # Combine lists and remove duplicates
        combined = list(set(existing[key] + new.get(key, [])))
        merged[key] = combined
    
    return merged
