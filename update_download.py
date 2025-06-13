with open('frontend/new.html', 'r') as f:
    content = f.read()

# Tìm và sửa phần download link
old_link = 'status.innerHTML += `<br><a href="http://localhost:8000/api/v2/outputs/${data.output_path}/download">Download Result</a>`;'
new_link = '''status.innerHTML += `<br><a href="http://localhost:8000/api/v2/outputs/${data.output_path}/download" download="${data.output_path}">Download Result</a>`;
                        // Auto download
                        const downloadLink = document.createElement('a');
                        downloadLink.href = `http://localhost:8000/api/v2/outputs/${data.output_path}/download`;
                        downloadLink.download = data.output_path || 'translated.txt';
                        document.body.appendChild(downloadLink);
                        downloadLink.click();
                        document.body.removeChild(downloadLink);'''

content = content.replace(old_link, new_link)

with open('frontend/new.html', 'w') as f:
    f.write(content)

print("Updated download functionality")
