from flask import Flask, request, jsonify
from pdf2json.extractor import read_pdf_and_group

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty file'}), 400
    result = read_pdf_and_group(file.stream)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8085)
