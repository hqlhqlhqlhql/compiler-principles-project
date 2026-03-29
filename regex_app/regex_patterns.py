import re

# Regular Expression Patterns

# 1. Mobile Phone (Chinese mainland: 1 followed by 10 digits, often with separators)
PHONE_PATTERN = r'(?:\+?86)?1[3-9]\d{9}'

# 2. Chinese Name (Usually 2-4 Chinese characters)
# We use a heuristic: words that are not part of the address or phone
NAME_PATTERN = r'[\u4e00-\u9fa5]{2,4}'

# 3. Address Pattern (Hierarchical: Province, City, District/County, Detail)
# This is a simplified version for demonstration
ADDRESS_PATTERN = (
    r'(?P<province>[^省]+省|.+自治区|[^市]+市)?'
    r'(?P<city>[^市]+?市|[^州]+?自治州|[^郡]+?郡)?'
    r'(?P<district>[^区]+?区|[^县]+?县|[^市]+?市|[^旗]+?旗)?'
    r'(?P<detail>.+)'
)

# 4. Combined logic to extract all
def extract_info(text):
    results = {
        "name": None,
        "phone": None,
        "province": None,
        "city": None,
        "district": None,
        "detail": None,
        "full_address": None
    }

    # Normalize input: replace commas with spaces
    text = text.replace(',', ' ').replace('，', ' ')

    # Extract Phone first (most unique pattern)
    phone_match = re.search(PHONE_PATTERN, text)
    if phone_match:
        results["phone"] = phone_match.group()
        text = text.replace(results["phone"], " ") 

    # Extract Address
    # Looking for keywords 省, 市, 区, 县, 旗 or digits for street numbers
    address_match = re.search(r'([\u4e00-\u9fa5]+[省市区县旗\d].+)', text)
    if address_match:
        full_addr = address_match.group(1).strip()
        results["full_address"] = full_addr
        
        # Parse hierarchy
        parts = re.match(ADDRESS_PATTERN, full_addr)
        if parts:
            results.update(parts.groupdict())
        
        # Remove the address part to search for the name
        text = text.replace(full_addr, " ")

    # Extract Name (Heuristic: what's left that matches name pattern)
    # Filter out common punctuation and empty spaces
    remaining_text = re.sub(r'[^\u4e00-\u9fa5]', ' ', text).strip()
    name_match = re.search(NAME_PATTERN, remaining_text)
    if name_match:
        results["name"] = name_match.group()

    return results
