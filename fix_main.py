with open('src/api/main.py', 'r') as f:
    lines = f.readlines()

# Find and fix the problematic section
for i in range(len(lines)):
    if 'chunk_size = 3000' in lines[i]:
        # Fix indentation - should be inside a try block
        lines[i] = '            chunk_size = 3000\n'
        break

with open('src/api/main.py', 'w') as f:
    f.writelines(lines)
    
print("Fixed main.py")
