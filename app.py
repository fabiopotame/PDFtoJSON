from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os
import tempfile
import logging
from datetime import datetime
from pdf2json.identify_document import analyze_document_by_type
from config import HOST, PORT, MAX_CONTENT_LENGTH
from db.oracle_connection import OracleManager

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@app.route('/')
def index():
    return send_file('static/index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "PDF to JSON API is running"})

@app.route('/oracle-info', methods=['GET'])
def oracle_info():
    """Returns information about Oracle configuration"""
    try:
        oracle_manager = OracleManager()
        info = oracle_manager.get_connection_info()
        
        return jsonify({
            "oracle_config": info,
            "connection_type": "TCP",
            "service_levels": list(info['service_levels'].keys())
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/documents/<int:document_id>/<filename>')
def serve_document(document_id, filename):
    """Serves stored PDF file"""
    try:
        file_path = os.path.join('documents', str(document_id), filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/documents', methods=['GET'])
def list_documents():
    """Lists all processed documents"""
    try:
        oracle_manager = OracleManager()
        documents = oracle_manager.get_all_documents()
        return jsonify({"documents": documents})
    except Exception as e:
        logging.error(f"Error listing documents: {e}")
        return jsonify({"error": "Error listing documents"}), 500

@app.route('/documents/<int:document_id>', methods=['GET'])
def get_document(document_id):
    """Gets specific document by ID"""
    try:
        oracle_manager = OracleManager()
        document = oracle_manager.get_document_by_id(document_id)
        if document:
            return jsonify(document)
        else:
            return jsonify({"error": "Document not found"}), 404
    except Exception as e:
        logging.error(f"Error getting document: {e}")
        return jsonify({"error": "Error getting document"}), 500

@app.route('/documents/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Removes document from database and file from disk"""
    try:
        oracle_manager = OracleManager()
        success = oracle_manager.delete_document(document_id)
        if success:
            return jsonify({"message": "Document deleted successfully"})
        else:
            return jsonify({"error": "Document not found"}), 404
    except Exception as e:
        logging.error(f"Error removing document: {e}")
        return jsonify({"error": "Error removing document"}), 500

@app.route('/document', methods=['POST'])
def analyze_document():
    """Processes PDF, saves to disk and stores in Oracle"""
    oracle_manager = OracleManager()
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '' or file.filename is None:
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "File must be a PDF"}), 400
    
    temp_file_path = None
    try:
        # Save temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        # Process document
        logging.info(f"Processing document: {file.filename}")
        result = analyze_document_by_type(temp_file_path)
        
        # Check if there was an error in processing
        if "error" in result:
            logging.error(f"Processing error: {result['error']}")
            return jsonify(result), 400
        
        # Extract document type from result
        document_type = result.get("document_type", "UNKNOWN")
        
        # Insert into Oracle and save file
        try:
            record_id, file_path = oracle_manager.insert_pdf_document(
                document_type=document_type,
                filename=file.filename,
                json_content=result,
                temp_file_path=temp_file_path
            )
            
            # Add database information to response
            result["database_id"] = record_id
            result["file_path"] = file_path
            result["stored_at"] = datetime.now().isoformat()
            
            logging.info(f"Document {file.filename} processed and stored with ID: {record_id}")
            
        except Exception as db_error:
            logging.error(f"Error saving to database/disk: {db_error}")
            # Continue returning JSON even if there's a database error
            result["database_warning"] = "Document processed but could not be saved to database"
        
        return jsonify(result)
    
    except Exception as e:
        logging.error(f"Error processing document: {e}")
        return jsonify({"error": str(e)}), 500
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
@app.route('/test-oracle', methods=['GET'])
def test_oracle():
    """Endpoint to test Oracle connection"""
    try:
        oracle_manager = OracleManager()
        if oracle_manager.test_connection():
            return jsonify({"status": "success", "message": "Oracle connection OK"})
        else:
            return jsonify({"status": "error", "message": "Oracle connection failed"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=False)
