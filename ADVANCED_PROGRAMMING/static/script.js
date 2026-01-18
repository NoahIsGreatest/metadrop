const input = document.getElementById('fileInput');
const bar = document.getElementById('progressBar');
const result = document.getElementById('result');

input.addEventListener('change', () => {
    const file = input.files[0];
    if (!file) return;

    const xhr = new XMLHttpRequest();
    const data = new FormData();
    data.append('file', file);

    xhr.open('POST', '/upload');

    xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
            const percent = (e.loaded / e.total) * 100;
            bar.style.width = percent + '%';
        }
    };

    xhr.onload = () => {
        if (xhr.status === 200) {
            const res = JSON.parse(xhr.responseText);
            result.innerHTML = `
                <img src="${res.qr_code}" />
                <p>Scan to download</p>
            `;
        } else {
            alert('Upload failed');
        }
    };

    xhr.send(data);
});
