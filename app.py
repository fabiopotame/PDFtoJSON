from flask import Flask, request, jsonify
from pdf2json.pdf_analyzer import read_pdf_and_analyze

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty file'}), 400
    result = read_pdf_and_analyze(file.stream)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8085)
