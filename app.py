from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
from pdf2json.pdf_line_parser import PDFLineParser
from pdf2json.pdf_analyzer import read_pdf_and_analyze

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "PDF to JSON API is running"})

@app.route('/analyze', methods=['POST'])
def analyze_pdf():
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
        
        with open(temp_file_path, 'rb') as pdf_file:
            result = read_pdf_and_analyze(pdf_file)
        
        os.unlink(temp_file_path)
        
        return jsonify(result)
    
    except Exception as e:
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
        return jsonify({"error": str(e)}), 500

@app.route('/analyze_line', methods=['POST'])
def analyze_line():
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
        
        parser = PDFLineParser()
        result = parser.parse_pdf(temp_file_path)
        
        os.unlink(temp_file_path)
        
        return jsonify(result)
    
    except Exception as e:
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
        return jsonify({"error": "Error processing PDF: {}".format(str(e))}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8085, debug=False)
