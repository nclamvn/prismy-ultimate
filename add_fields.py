with open('frontend/index.html', 'r') as f:
    lines = f.readlines()

# Find line with file input
for i, line in enumerate(lines):
    if 'type="file"' in line and 'pdf-file' in line:
        # Add language and tier selectors after file input
        lines.insert(i+1, '''            <div style="margin: 15px 0;">
                <label style="margin-right: 10px;">Target Language:</label>
                <select id="targetLanguage" style="padding: 5px; margin-right: 20px;">
                    <option value="vi">Vietnamese</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                </select>
                <label style="margin-right: 10px;">Quality:</label>
                <select id="tier" style="padding: 5px;">
                    <option value="standard">Standard (GPT-4)</option>
                    <option value="premium">Premium (GPT-4 + Claude)</option>
                </select>
            </div>
''')
        break

# Find FormData section and add fields
for i, line in enumerate(lines):
    if "formData.append('file', file)" in line:
        lines.insert(i+1, '''                formData.append('target_language', document.getElementById('targetLanguage').value);
                formData.append('tier', document.getElementById('tier').value);
''')
        break

with open('frontend/index.html', 'w') as f:
    f.writelines(lines)

print("Fields added!")
