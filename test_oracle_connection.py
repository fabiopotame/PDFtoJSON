#!/usr/bin/env python3
"""
Teste de conexão Oracle
Verifica se a conexão com o banco Oracle está funcionando corretamente
"""

import os
import sys
import oracledb
from dotenv import load_dotenv
import logging
import subprocess

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

def test_oracle_connection():
    """Testar conexão Oracle via TCP"""
    try:
        username = os.getenv('ORACLE_USER')
        password = os.getenv('ORACLE_PASSWORD')
        host = os.getenv('ORACLE_HOST')
        port = int(os.getenv('ORACLE_PORT'))
        service_name = os.getenv('ORACLE_SERVICE_NAME')

        if not password:
            logger.error("ORACLE_PASSWORD não encontrado nas variáveis de ambiente")
            return False

        # Listar conteúdo do Instant Client antes de tentar ativar o modo thick
        logger.info('Conteúdo de /instantclient:')
        try:
            output = subprocess.check_output(['ls', '-l', '/instantclient']).decode()
            logger.info('\n' + output)
        except Exception as e:
            logger.error(f'Erro ao listar /instantclient: {e}')

        try:
            if os.path.isdir("/instantclient"):
                logger.info(f"[INFO] Ativando modo thick com Oracle Client: /instantclient")
                oracledb.init_oracle_client(lib_dir="/instantclient")
            else:
                logger.info(f"[INFO] Instant Client não encontrado em /instantclient, usando modo thin.")
        except Exception as e:
            logger.error(f"[ERRO] Falha ao iniciar modo thick: {e}")
            logger.info("[INFO] Continuando em modo thin.")


        logger.info(f"Tentando conectar com usuário: {username}")
        logger.info(f"Host: {host}, User: {username}, Senha: {password}, Porta: {port}, Service Name: {service_name}")

        dsn = oracledb.makedsn(host, port, service_name=service_name)
        oracledb.init_oracle_client(lib_dir="/home/ega/instantclient_21_13")
        connection = oracledb.connect(user=username, password=password, dsn=dsn)

        logger.info("✅ Conexão Oracle estabelecida com sucesso!")

        # Testar uma query simples
        cursor = connection.cursor()
        cursor.execute("SELECT SYSDATE FROM DUAL")
        result = cursor.fetchone()
        logger.info(f"✅ Query de teste executada com sucesso. Data atual: {result[0]}")

        # Verificar versão do Oracle
        cursor.execute("SELECT * FROM v$version WHERE ROWNUM = 1")
        version = cursor.fetchone()
        logger.info(f"✅ Versão do Oracle: {version[0]}")

        # Verificar se a tabela PDFTOJSON existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM user_tables 
            WHERE table_name = 'PDFTOJSON'
        """)
        table_count = cursor.fetchone()[0]

        if table_count > 0:
            logger.info("✅ Tabela PDFTOJSON encontrada")
            cursor.execute("SELECT COUNT(*) FROM PDFTOJSON")
            record_count = cursor.fetchone()[0]
            logger.info(f"✅ Tabela PDFTOJSON possui {record_count} registros")
        else:
            logger.warning("⚠️ Tabela PDFTOJSON não encontrada")

        # Verificar views
        views_to_check = ['VW_PDFTOJSON_SECTIONS', 'VW_PDFTOJSON_FIELDS', 'vw_pdftojson_full']
        for view_name in views_to_check:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM user_views 
                WHERE view_name = :view_name
            """, view_name=view_name.upper())
            view_count = cursor.fetchone()[0]

            if view_count > 0:
                logger.info(f"✅ View {view_name} encontrada")
            else:
                logger.warning(f"⚠️ View {view_name} não encontrada")

        cursor.close()
        connection.close()

        logger.info("✅ Teste de conexão concluído com sucesso!")
        return True

    except Exception as e:
        logger.error(f"❌ Erro ao conectar com Oracle: {e}")
        return False

def main():
    """Função principal"""
    logger.info("Iniciando teste de conexão Oracle...")

    # Testar conexão
    if not test_oracle_connection():
        logger.error("Falha no teste de conexão")
        sys.exit(1)

    logger.info("🎉 Todos os testes passaram com sucesso!")

if __name__ == "__main__":
    main() 