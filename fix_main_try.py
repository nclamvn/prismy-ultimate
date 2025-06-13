with open('src/api/main.py', 'r') as f:
    lines = f.readlines()

# Find where we need to add except
for i in range(len(lines)):
    if 'translated_text += f"\\n[Translation error' in lines[i]:
        # This except belongs to inner try, need to add except for outer try
        # Insert except before "Store complete translation"
        for j in range(i+1, len(lines)):
            if '# Store complete translation' in lines[j]:
                lines.insert(j, '        except Exception as e:\n')
                lines.insert(j+1, '            translated_text = f"Translation failed: {str(e)}"\n')
                lines.insert(j+2, '\n')
                break
        break

with open('src/api/main.py', 'w') as f:
    f.writelines(lines)
    
print("Fixed try/except blocks")
