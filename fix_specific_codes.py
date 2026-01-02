import re

# Read the test file
with open('tests/unit/test_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix specific cases that should be 500, not 401
# Database errors should be 500
content = re.sub(r'side_effect=HTTPException\(status_code=500, detail="Database.*?"\)\):\s+response = client\.(get|post|put|delete)\(.*?\)\s+assert response\.status_code == 401', 
                lambda m: m.group(0).replace('assert response.status_code == 401', 'assert response.status_code == 500'), content)

# Timeout errors should be 500  
content = re.sub(r'side_effect=HTTPException\(status_code=500, detail=".*?timeout.*?"\)\):\s+response = client\.(get|post|put|delete)\(.*?\)\s+assert response\.status_code == 401', 
                lambda m: m.group(0).replace('assert response.status_code == 401', 'assert response.status_code == 500'), content, flags=re.IGNORECASE)

# Write back the fixed content
with open('tests/unit/test_api.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed specific status code expectations in test_api.py")