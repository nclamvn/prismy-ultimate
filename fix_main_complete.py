with open('src/api/main.py', 'r') as f:
    content = f.read()

# Fix the indentation issue
content = content.replace(
    '''        # Translate complete text
        translated_text = ""
            # Split into manageable chunks
            chunk_size = 3000''',
    '''        # Translate complete text
        translated_text = ""
        try:
            # Split into manageable chunks
            chunk_size = 3000'''
)

with open('src/api/main.py', 'w') as f:
    f.write(content)
    
print("Fixed main.py completely")
