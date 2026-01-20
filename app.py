from flask import Flask, request, jsonify, render_template, send_from_directory, url_for
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import os, uuid, time, threading, qrcode

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

UPLOAD_FOLDER = 'uploads'
QR_FOLDER = 'qrcodes'

FREE_MAX_SIZE = 50 * 1024 * 1024  # 50MB free tier
AUTO_DELETE_AFTER = 15 * 60  # 15 minutes

app.config['MAX_CONTENT_LENGTH'] = FREE_MAX_SIZE

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

file_registry = {}  # filename -> upload_time


def auto_delete_worker():
    while True:
        now = time.time()
        for filename, timestamp in list(file_registry.items()):
            if now - timestamp > AUTO_DELETE_AFTER:
                try:
                    os.remove(os.path.join(UPLOAD_FOLDER, filename))
                    os.remove(os.path.join(QR_FOLDER, f"{filename}.png"))
                except:
                    pass
                file_registry.pop(filename, None)
        time.sleep(60)


threading.Thread(target=auto_delete_worker, daemon=True).start()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    unique_name = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_name)
    file.save(file_path)

    file_registry[unique_name] = time.time()

    download_url = url_for('download_file', filename=unique_name, _external=True)

    qr = qrcode.make(download_url)
    qr.save(os.path.join(QR_FOLDER, f"{unique_name}.png"))

    return jsonify({
        'download_url': download_url,
        'qr_code': url_for('get_qr', filename=f"{unique_name}.png")
    })


@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        return "File expired or deleted :(", 404
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route('/qr/<filename>')
def get_qr(filename):
    return send_from_directory(QR_FOLDER, filename)


if __name__ == '__main__':
    app.run(debug=True)


