import oracledb
import json
import os
import shutil
from datetime import datetime
from config import ORACLE_CONFIG
import logging

def get_oracle_connection():
    """
    Retorna uma conexão Oracle, ativando modo thick se possível.
    """
    import oracledb
    import os
    import logging
    from config import ORACLE_CONFIG
    try:
        # Ativar modo thick
        try:
            if os.path.isdir("/instantclient"):
                logging.info("[INFO] Ativando modo thick com Oracle Client: /instantclient")
                oracledb.init_oracle_client(lib_dir="/instantclient")
            else:
                logging.info("[INFO] Instant Client não encontrado em /instantclient, usando modo thin.")
        except Exception as e:
            logging.error(f"[ERRO] Falha ao iniciar modo thick: {e}")
            logging.info("[INFO] Continuando em modo thin.")

        dsn = oracledb.makedsn(
            ORACLE_CONFIG['host'],
            ORACLE_CONFIG['port'],
            service_name=ORACLE_CONFIG['service_name']
        )
        connection = oracledb.connect(
            user=ORACLE_CONFIG['user'],
            password=ORACLE_CONFIG['password'],
            dsn=dsn,
            encoding=ORACLE_CONFIG['encoding']
        )
        return connection
    except Exception as e:
        logging.error(f"Error connecting to Oracle: {e}")
        return None

class OracleManager:
    def __init__(self):
        self.config = ORACLE_CONFIG
        self.documents_path = "documents"
        
    def get_connection(self):
        """Create Oracle TCP connection"""
        try:
            # Ativar modo thick
            try:
                if os.path.isdir("/instantclient"):
                    logging.info(f"[INFO] Ativando modo thick com Oracle Client: /instantclient")
                    oracledb.init_oracle_client(lib_dir="/instantclient")
                else:
                    logging.info(f"[INFO] Instant Client não encontrado em /instantclient, usando modo thin.")
            except Exception as e:
                logging.error(f"[ERRO] Falha ao iniciar modo thick: {e}")
                logging.info("[INFO] Continuando em modo thin.")

            dsn = oracledb.makedsn(
                self.config['host'], 
                self.config['port'], 
                service_name=self.config['service_name']
            )
            connection = oracledb.connect(
                user=self.config['user'],
                password=self.config['password'],
                dsn=dsn,
                encoding=self.config['encoding']
            )
            return connection
        except Exception as e:
            logging.error(f"Error connecting to Oracle: {e}")
            return None
    
    def ensure_documents_directory(self):
        """Ensure documents folder exists"""
        if not os.path.exists(self.documents_path):
            os.makedirs(self.documents_path)
            logging.info(f"Folder {self.documents_path} created")
    
    def create_document_directory(self, document_id):
        """Create specific directory for document"""
        # Convert to integer to avoid folders with .0
        document_id_int = int(document_id)
        document_dir = os.path.join(self.documents_path, str(document_id_int))
        if not os.path.exists(document_dir):
            os.makedirs(document_dir)
            logging.info(f"Directory created: {document_dir}")
        return document_dir
    
    def save_pdf_file(self, document_id, filename, temp_file_path):
        """Save PDF file to specific directory"""
        try:
            # Create directory for document
            document_dir = self.create_document_directory(document_id)
            
            # Final file path
            final_path = os.path.join(document_dir, filename)
            
            # Copy temporary file to final destination
            shutil.copy2(temp_file_path, final_path)
            
            # Return relative path to save in database
            # Convert to integer to avoid folders with .0
            document_id_int = int(document_id)
            relative_path = os.path.join(str(document_id_int), filename)
            relative_path = os.path.join(self.documents_path, relative_path)
            
            logging.info(f"File saved: {final_path}")
            return relative_path
            
        except Exception as e:
            logging.error(f"Error saving file: {e}")
            raise
            
    def insert_pdf_document(self, document_type, filename, json_content, temp_file_path):
        """Insert processed document in database and save file"""
        connection = None
        try:
            # Ensure documents folder exists
            self.ensure_documents_directory()
            
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Insert record in database first to get ID
            sql = """
                INSERT INTO PDFTOJSON (DOCUMENT_TYPE, DOCUMENT_FILENAME, DOCUMENT_PATH, CONTENT)
                VALUES (:document_type, :filename, :path, :content)
                RETURNING ID INTO :id
            """
            
            # Variable to capture returned ID
            id_var = cursor.var(oracledb.NUMBER)
            
            # Insert with temporary path
            cursor.execute(sql, {
                'document_type': document_type,
                'filename': filename,
                'path': 'temp',  # Temporary, will be updated
                'content': json.dumps(json_content, ensure_ascii=False),
                'id': id_var
            })
            
            # Get ID of inserted record
            record_id = id_var.getvalue()[0]
            
            # Save PDF file using ID
            file_path = self.save_pdf_file(record_id, filename, temp_file_path)
            
            # Update path in database
            update_sql = """
                UPDATE PDFTOJSON 
                SET DOCUMENT_PATH = :path 
                WHERE ID = :id
            """
            
            cursor.execute(update_sql, {
                'path': file_path,
                'id': record_id
            })
            
            connection.commit()
            
            logging.info(f"Document '{filename}' inserted with ID: {record_id}")
            return record_id, file_path
            
        except Exception as e:
            if connection:
                connection.rollback()
            logging.error(f"Error inserting document: {e}")
            raise
        finally:
            if connection:
                connection.close()
                
    def get_document_by_id(self, document_id):
        """Get document by ID"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            sql = """
                SELECT ID, DOCUMENT_TYPE, DOCUMENT_FILENAME, DOCUMENT_PATH, CONTENT, DATE_CREATED
                FROM PDFTOJSON
                WHERE ID = :id
            """
            
            cursor.execute(sql, {'id': document_id})
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'document_type': row[1],
                    'document_filename': row[2],
                    'document_path': row[3],
                    'content': json.loads(row[4]),
                    'date_created': row[5].isoformat()
                }
            return None
            
        except Exception as e:
            logging.error(f"Error getting document: {e}")
            raise
        finally:
            if connection:
                connection.close()
                
    def get_all_documents(self, limit=50):
        """List all documents (with limit)"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            sql = """
                SELECT ID, DOCUMENT_TYPE, DOCUMENT_FILENAME, DOCUMENT_PATH, DATE_CREATED
                FROM PDFTOJSON
                ORDER BY DATE_CREATED DESC
                FETCH FIRST :limit ROWS ONLY
            """
            
            cursor.execute(sql, {'limit': limit})
            rows = cursor.fetchall()
            
            documents = []
            for row in rows:
                documents.append({
                    'id': row[0],
                    'document_type': row[1],
                    'document_filename': row[2],
                    'document_path': row[3],
                    'date_created': row[4].isoformat()
                })
            
            return documents
            
        except Exception as e:
            logging.error(f"Error listing documents: {e}")
            raise
        finally:
            if connection:
                connection.close()
                
    def get_document_file_path(self, document_id):
        """Return complete PDF file path"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            sql = """
                SELECT DOCUMENT_PATH 
                FROM PDFTOJSON 
                WHERE ID = :id
            """
            
            cursor.execute(sql, {'id': document_id})
            row = cursor.fetchone()
            
            if row:
                return row[0]
            return None
            
        except Exception as e:
            logging.error(f"Error getting file path: {e}")
            raise
        finally:
            if connection:
                connection.close()
                
    def delete_document(self, document_id):
        """Remove document from database and file from disk"""
        connection = None
        try:
            # Get file path before deleting
            file_path = self.get_document_file_path(document_id)
            
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Delete from database
            sql = "DELETE FROM PDFTOJSON WHERE ID = :id"
            cursor.execute(sql, {'id': document_id})
            
            connection.commit()
            
            # Delete file from disk if exists
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"File removed: {file_path}")
                
                # Try to remove directory if empty
                dir_path = os.path.dirname(file_path)
                try:
                    os.rmdir(dir_path)
                    logging.info(f"Directory removed: {dir_path}")
                except OSError:
                    pass  # Directory not empty
            
            logging.info(f"Document ID {document_id} removed")
            return True
            
        except Exception as e:
            if connection:
                connection.rollback()
            logging.error(f"Error removing document: {e}")
            raise
        finally:
            if connection:
                connection.close()
                
    def get_status(self):
        """Get connection status"""
        try:
            connection = self.get_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute("SELECT 1 FROM DUAL")
                result = cursor.fetchone()
                cursor.close()
                connection.close()
                
                return {
                    'status': 'connected',
                    'message': 'Oracle connection successful',
                    'connection_type': 'TCP'
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'connection_type': 'TCP'
            }
            
    def get_connection_info(self):
        """Return information about configured connection"""
        return {
            'user': self.config['user'],
            'host': self.config['host'],
            'port': self.config['port'],
            'service_name': self.config['service_name'],
            'encoding': self.config['encoding']
        } 