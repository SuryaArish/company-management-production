import re

# Read the test file
with open('tests/unit/test_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all incorrect import paths
content = re.sub(r"@patch\('handlers\.", "@patch('app.api.handlers.", content)
content = re.sub(r"with patch\('handlers\.", "with patch('app.api.handlers.", content)

# Write back the fixed content
with open('tests/unit/test_api.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed all import paths in test_api.py")