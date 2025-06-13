with open('src/services/queue/manager.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip_next = 0

for i, line in enumerate(lines):
    if skip_next > 0:
        skip_next -= 1
        continue
        
    # Skip duplicate "Also queue to Celery" block
    if '# Also queue to Celery' in line:
        # Skip this line and next 2 lines
        skip_next = 2
        continue
        
    new_lines.append(line)

with open('src/services/queue/manager.py', 'w') as f:
    f.writelines(new_lines)

print("Cleaned up duplicates!")
