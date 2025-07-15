from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os
import tempfile
from pdf2json.identify_document import analyze_document_by_type
from config import HOST, PORT, MAX_CONTENT_LENGTH

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
CORS(app)

@app.route('/')
def index():
    return send_file('static/index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "PDF to JSON API is running"})

@app.route('/document', methods=['POST'])
def analyze_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '' or file.filename is None:
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "File must be a PDF"}), 400
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        result = analyze_document_by_type(temp_file_path)
        
        os.unlink(temp_file_path)
        
        return jsonify(result)
    
    except Exception as e:
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=False)
