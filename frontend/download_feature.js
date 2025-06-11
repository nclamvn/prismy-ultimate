// Thêm nút download sau khi có kết quả
function addDownloadButton(results) {
    const downloadBtn = document.createElement('button');
    downloadBtn.textContent = '📥 Download Kết Quả';
    downloadBtn.style.cssText = 'background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 5px; margin: 10px; cursor: pointer;';
    
    downloadBtn.onclick = function() {
        // Download as JSON
        const blob = new Blob([JSON.stringify(results, null, 2)], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `prismy_result_${Date.now()}.json`;
        a.click();
        
        // Download extracted text
        const textBlob = new Blob([results.extraction.text], {type: 'text/plain'});
        const textUrl = URL.createObjectURL(textBlob);
        const textLink = document.createElement('a');
        textLink.href = textUrl;
        textLink.download = `extracted_text_${Date.now()}.txt`;
        textLink.click();
    };
    
    document.getElementById('results').appendChild(downloadBtn);
}
