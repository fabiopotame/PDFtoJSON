#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser Baseado em Linhas Fixas - Extrai campos diretamente pelas linhas do PDF
"""

import re
import json
import pdfplumber
from collections import defaultdict

class PDFLineParser:
    def __init__(self):
        # Mapeamento de campos por linha (baseado no PDF 55600-demo.pdf)
        self.field_mapping = {
            # Header (linha 2)
            2: {
                'header.capa': {'start': 'CAPA:', 'end': 'DEMONSTRATIVO:'},
                'header.demonstrativo': {'start': 'DEMONSTRATIVO:', 'end': 'NOTA FISCAL:'},
                'header.nota_fiscal': {'start': 'NOTA FISCAL:', 'end': None}
            },
            # Regime (linha 3)
            3: {
                'header.regime': {'start': 'Regime:', 'end': None}
            },
            # Tarifa 01 (linha 4)
            4: {
                'header.tarifa 01': {'start': 'Tarifa 01:', 'end': None}
            },
            # Opção tarifa (linha 5)
            5: {
                'header.opcao_tarifa': {'start': 'Opção tarifa:', 'end': None}
            },
            # Beneficiário (linha 7)
            7: {
                'beneficiario.codigo': {'start': 'Código:', 'end': 'Nome:'},
                'beneficiario.nome': {'start': 'Nome:', 'end': 'CNPJ/CPF:'},
                'beneficiario.cnpj_cpf': {'start': 'CNPJ/CPF:', 'end': None}
            },
            # Comissária (linha 9)
            9: {
                'comissaria.codigo': {'start': 'Código:', 'end': 'Nome:'},
                'comissaria.nome': {'start': 'Nome:', 'end': 'CNPJ/CPF:'},
                'comissaria.cnpj_cpf': {'start': 'CNPJ/CPF:', 'end': None}
            },
            # Cliente (linha 11)
            11: {
                'cliente.codigo': {'start': 'Código:', 'end': 'Nome:'},
                'cliente.nome': {'start': 'Nome:', 'end': None}
            },
            # Cliente endereço (linha 12)
            12: {
                'cliente.endereco': {'start': 'Endereço:', 'end': None}
            },
            # Cliente bairro, cidade, estado, cep (linha 13)
            13: {
                'cliente.bairro': {'start': 'Bairro:', 'end': 'Cidade:'},
                'cliente.cidade': {'start': 'Cidade:', 'end': 'Estado:'},
                'cliente.estado': {'start': 'Estado:', 'end': 'CEP:'},
                'cliente.cep': {'start': 'CEP:', 'end': None}
            },
            # Cliente CNPJ/CPF, IE (linha 14)
            14: {
                'cliente.cnpj_cpf': {'start': 'CNPJ/CPF:', 'end': 'IE:'},
                'cliente.ie': {'start': 'IE:', 'end': None}
            },
            # Faturar para (linha 16)
            16: {
                'faturar para.codigo': {'start': 'Código:', 'end': 'Nome:'},
                'faturar para.nome': {'start': 'Nome:', 'end': None}
            },
            # Faturar para endereço (linha 17)
            17: {
                'faturar para.endereco': {'start': 'Endereço:', 'end': None}
            },
            # Faturar para bairro, cidade, estado, cep (linha 18)
            18: {
                'faturar para.bairro': {'start': 'Bairro:', 'end': 'Cidade:'},
                'faturar para.cidade': {'start': 'Cidade:', 'end': 'Estado:'},
                'faturar para.estado': {'start': 'Estado:', 'end': 'CEP:'},
                'faturar para.cep': {'start': 'CEP:', 'end': None}
            },
            # Faturar para CNPJ/CPF, IE (linha 19)
            19: {
                'faturar para.cnpj_cpf': {'start': 'CNPJ/CPF:', 'end': 'IE:'},
                'faturar para.ie': {'start': 'IE:', 'end': None}
            },
            # Tarifas aplicadas (linha 21)
            21: {
                'tarifas aplicadas.moeda': {'start': 'Moeda:', 'end': 'Data/Cotação:'},
                'tarifas aplicadas.cotacao': {'start': 'Data/Cotação:', 'end': 'Valor:'},
                'tarifas aplicadas.valor_cotacao': {'start': 'Valor:', 'end': None}
            }
        }

    def extract_text_by_lines(self, pdf_path):
        """Extrai texto do PDF linha a linha"""
        lines = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    page_lines = text.split('\n')
                    for line in page_lines:
                        if line.strip():
                            lines.append(line.strip())
        return lines

    def extract_field_value(self, line_text, field_config):
        """Extrai valor de um campo específico da linha"""
        if not line_text:
            return ""
        
        start_marker = field_config['start']
        end_marker = field_config['end']
        
        if start_marker is None:
            # Se não há marcador de início, retorna a linha inteira
            return line_text.strip()
        
        # Encontra o início do valor
        start_pos = line_text.find(start_marker)
        if start_pos == -1:
            return ""
        
        # Remove o marcador de início
        value_start = start_pos + len(start_marker)
        
        if end_marker is None:
            # Se não há marcador de fim, pega até o final da linha
            value = line_text[value_start:].strip()
        else:
            # Encontra o fim do valor
            end_pos = line_text.find(end_marker, value_start)
            if end_pos == -1:
                value = line_text[value_start:].strip()
            else:
                value = line_text[value_start:end_pos].strip()
        
        return value

    def parse_pdf(self, pdf_path):
        """Parse do PDF usando mapeamento de linhas fixas"""
        lines = self.extract_text_by_lines(pdf_path)
        
        result = {
            'header': {},
            'beneficiario': {},
            'comissaria': {},
            'cliente': {},
            'faturar para': {},
            'tarifas aplicadas': {},
            'armazenagem': {'fields': [], 'total_armazenagem_periodos': 0.0},
            'operacao_servicos': {'fields': [], 'total_operacao_servicos': 0.0, 'total_geral': 0.0},
            'observacoes': '',
            'informacoes do lote': {}
        }
        
        for line_num, field_configs in self.field_mapping.items():
            if line_num <= len(lines):
                line_text = lines[line_num - 1]
                
                for field_name, config in field_configs.items():
                    value = self.extract_field_value(line_text, config)
                    if value:
                        self.set_nested_value(result, field_name, value)
        
        self.parse_dynamic_tables(lines, result)
        
        lote_section = {}
        
        lote_line = None
        doc_aduaneiro_line = None
        valores_line = None
        ref_line = None
        
        for i, line in enumerate(lines):
            if re.match(r'^\d{12}\s+\w+', line):
                lote_line = i
            elif re.match(r'^DI\s+-\s+\d{4}/\d+', line):
                doc_aduaneiro_line = i
            elif re.match(r'^\d+\.\d+,\d+\s+\d+\.\d+,\d+', line):
                valores_line = i
            elif 'Ref.Cliente:' in line:
                ref_line = i
        
        if lote_line is not None and lote_line < len(lines):
            lote_text = lines[lote_line]
            
            lote_match = re.match(r'^(\d{12})', lote_text)
            if lote_match:
                lote_section['lote'] = lote_match.group(1)
            
            parts = lote_text.split()
            if len(parts) >= 2:
                candidate = parts[1]
                if re.match(r'^[A-Z]{4,5}\d{8,10}$', candidate):
                    lote_section['bl_awb_ctrc'] = candidate
                else:
                    lote_section['bl_awb_ctrc'] = None
            else:
                lote_section['bl_awb_ctrc'] = None
            
            doc_entrada_match = re.search(r'([A-Z]{3}\s*-\s*\d{2}/\d+)\s*-\s*([A-Z0-9]+)', lote_text)
            if doc_entrada_match:
                lote_section['doc_aduan_de_entrada'] = f"{doc_entrada_match.group(1)} - {doc_entrada_match.group(2)}"
        
        if doc_aduaneiro_line is not None and doc_aduaneiro_line < len(lines):
            doc_text = lines[doc_aduaneiro_line]
            doc_match = re.search(r'DI\s+-\s+(\d{4}/\d+)', doc_text)
            if doc_match:
                lote_section['doc_aduaneiro_i'] = f"DI - {doc_match.group(1)}"
            
            data_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(\d+)', doc_text)
            if data_match:
                lote_section['data_entrada'] = data_match.group(1)
                lote_section['qtd_container'] = data_match.group(2)
        
        if ref_line is not None and ref_line < len(lines):
            ref_text = lines[ref_line]
            if re.search(r'Ref\.Cliente:\s*$', ref_text):
                if ref_line + 1 < len(lines):
                    next_line = lines[ref_line + 1]
                    if next_line:
                        parts = next_line.split(' - ')
                        if len(parts) > 1:
                            ref_value = parts[-1].strip()
                            if ref_value.startswith('NVT '):
                                ref_value = ref_value[4:]
                            
                            if re.match(r'^\d{1,3}$', ref_value):
                                if 'doc_aduan_de_entrada' in lote_section:
                                    doc_entrada = lote_section['doc_aduan_de_entrada']
                                    if doc_entrada and doc_entrada.endswith(f" - {ref_value}"):
                                        lote_section['ref_cliente'] = None
                                    else:
                                        lote_section['ref_cliente'] = ref_value
                                else:
                                    lote_section['ref_cliente'] = ref_value
                            else:
                                lote_section['ref_cliente'] = ref_value
                        else:
                            ref_cliente_match = re.search(r'([A-Z0-9]+(?:[,\-][A-Z0-9]+)*)\s*$', next_line)
                            if ref_cliente_match:
                                ref_value = ref_cliente_match.group(1)
                                if re.match(r'^\d{1,3}$', ref_value):
                                    if 'doc_aduan_de_entrada' in lote_section:
                                        doc_entrada = lote_section['doc_aduan_de_entrada']
                                        if doc_entrada and doc_entrada.endswith(f" - {ref_value}"):
                                            lote_section['ref_cliente'] = None
                                        else:
                                            lote_section['ref_cliente'] = ref_value
                                    else:
                                        lote_section['ref_cliente'] = ref_value
                                else:
                                    lote_section['ref_cliente'] = ref_value
                            else:
                                lote_section['ref_cliente'] = None
                    else:
                        lote_section['ref_cliente'] = None
            else:
                ref_match = re.search(r'Ref\.Cliente:\s*([A-Z0-9\s,.-]+)', ref_text)
                if ref_match:
                    ref_value = ref_match.group(1).strip()
                    if ref_value:
                        lote_section['ref_cliente'] = ref_value
                    else:
                        lote_section['ref_cliente'] = None
                else:
                    lote_section['ref_cliente'] = None
        else:
            lote_section['ref_cliente'] = None
        
        if valores_line is not None and valores_line < len(lines):
            valores_text = lines[valores_line]
            valores_match = re.search(r'(\d+\.\d+,\d+)\s+(\d+\.\d+,\d+)', valores_text)
            if valores_match:
                lote_section['valor_fob_cif_rs'] = float(valores_match.group(1).replace('.', '').replace(',', '.'))
                lote_section['valor_fob_cif_us'] = float(valores_match.group(2).replace('.', '').replace(',', '.'))
            
            qtd_match = re.search(r'(\d+\.\d+,\d+)\s+(\d+\.\d+,\d+)\s+(\d+\.\d{2})', valores_text)
            if qtd_match:
                lote_section['qtd_lote'] = qtd_match.group(3)
            
            datas_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})', valores_text)
            if datas_match:
                lote_section['periodos_apuracao'] = f"{datas_match.group(1)} a {datas_match.group(2)}"
                lote_section['fim_periodo_armaz'] = datas_match.group(2)
                lote_section['prazo_p_retirada'] = datas_match.group(2)
        
        if valores_line is not None:
            for offset in range(1, 6):
                idx = valores_line + offset
                if idx < len(lines):
                    line = lines[idx]
                    datas_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})', line)
                    if datas_match:
                        lote_section['periodos_apuracao'] = f"{datas_match.group(1)} a {datas_match.group(2)}"
                        lote_section['fim_periodo_armaz'] = datas_match.group(2)
                        lote_section['prazo_p_retirada'] = datas_match.group(2)
                    dias_match = re.search(r'Dias:\s*(\d+)', line)
                    if dias_match:
                        lote_section['dias'] = dias_match.group(1)
                    periodos_match = re.search(r'Perío[^:]*:\s*(\d+)', line)
                    if periodos_match:
                        lote_section['periodos_armaz'] = periodos_match.group(1)
        
        if 'dias' not in lote_section:
            for i, line in enumerate(lines):
                if 'Dias:' in line:
                    dias_match = re.search(r'Dias:\s*(\d+)', line)
                    if dias_match:
                        lote_section['dias'] = dias_match.group(1)
                        break
        if 'periodos_armaz' not in lote_section:
            for i, line in enumerate(lines):
                if 'Perío' in line and ':' in line:
                    periodos_match = re.search(r'Perío[^:]*:\s*(\d+)', line)
                    if periodos_match:
                        lote_section['periodos_armaz'] = periodos_match.group(1)
                        break
        
        lote_section.setdefault('doc_aduaneiro_ii', '')
        lote_section.setdefault('bl_awb_ctrc', None)
        
        if 'faturar para' in result:
            result['faturar para']['im'] = None
        
        if 'observacoes' not in result:
            result['observacoes'] = ''
        
        if 'periodos_apuracao' in lote_section:
            try:
                from datetime import datetime
                datas_text = lote_section['periodos_apuracao']
                datas_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})', datas_text)
                if datas_match:
                    data_inicio = datetime.strptime(datas_match.group(1), '%d/%m/%Y')
                    data_fim = datetime.strptime(datas_match.group(2), '%d/%m/%Y')
                    dias = (data_fim - data_inicio).days + 1
                    lote_section['dias'] = str(dias)
            except Exception as e:
                lote_section['dias'] = None
        
        if 'armazenagem' in result and 'fields' in result['armazenagem']:
            periodos = len(result['armazenagem']['fields'])
            lote_section['periodos_armaz'] = str(periodos)
        else:
            lote_section['periodos_armaz'] = None
        
        result['informacoes do lote'] = lote_section
        
        self.clean_prefixes(result)
        
        if 'operacao_servicos' in result and 'fields' in result['operacao_servicos']:
            for field in result['operacao_servicos']['fields']:
                if 'descricao' in field:
                    field['descricao'] = self.normalize_string(field['descricao'])
        
        if 'armazenagem' in result and 'fields' in result['armazenagem']:
            for field in result['armazenagem']['fields']:
                if '%_armaz' in field:
                    field['%_armaz'] = self.normalize_number(field['%_armaz'])
        
        if 'operacao_servicos' in result:
            if 'total_geral' in result['operacao_servicos']:
                result['operacao_servicos']['total_geral'] = self.round_decimal(result['operacao_servicos']['total_geral'])
            if 'total_operacao_servicos' in result['operacao_servicos']:
                result['operacao_servicos']['total_operacao_servicos'] = self.round_decimal(result['operacao_servicos']['total_operacao_servicos'])
        
        return result

    def set_nested_value(self, data, field_path, value):
        """Define valor em estrutura aninhada usando dot notation"""
        keys = field_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value

    def parse_dynamic_tables(self, lines, result):
        """Parse das tabelas dinâmicas (armazenagem e operações)"""
        armazenagem_line = None
        operacao_line = None
        
        for i, line in enumerate(lines):
            if 'A R M A Z E N A G E M' in line:
                armazenagem_line = i
            elif 'O P E R A Ç Ã O / S E R V I Ç O S' in line:
                operacao_line = i
        
        if armazenagem_line is not None:
            self.parse_armazenagem_table(lines, armazenagem_line, result)
        
        if operacao_line is not None:
            self.parse_operacao_table(lines, operacao_line, result)

    def parse_armazenagem_table(self, lines, start_line, result):
        """Parse da tabela de armazenagem"""
        current_line = start_line + 2
        total_armazenagem = 0.0
        
        while current_line < len(lines):
            line = lines[current_line]
            
            if 'Total de Armazenagem' in line or 'O P E R A Ç Ã O' in line:
                break
            
            if line.strip() and not line.startswith('Período'):
                parts = line.split()
                if len(parts) >= 8:
                    try:
                        valor = float(parts[7].replace(',', '.'))
                        total_armazenagem += valor
                    except:
                        valor = parts[7]
                    
                    armazenagem_item = {
                        'periodo': parts[0],
                        'inicio': parts[1],
                        'final': parts[2],
                        'qtde_pecas': parts[3],
                        'carregado': parts[4],
                        'saldo': parts[5],
                        '%_armaz': parts[6],
                        'total_armaz_rs': valor
                    }
                    result['armazenagem']['fields'].append(armazenagem_item)
            
            current_line += 1
        
        result['armazenagem']['total_armazenagem_periodos'] = total_armazenagem

    def parse_operacao_table(self, lines, start_line, result):
        """Parse da tabela de operações/serviços"""
        current_line = start_line + 2
        total_operacao = 0.0
        total_geral = 0.0
        
        while current_line < len(lines):
            line = lines[current_line]
            
            if 'Total Operação' in line or 'Total Geral' in line or 'O B S E R V A Ç' in line:
                break
            
            if line.strip() and not line.startswith('Descrição'):
                match = re.match(r'(\d+)\s*-\s*(.+?)\s+(\d+\.?\d*)\s+([\d,]+)\s+([\d,]+)', line)
                if match:
                    try:
                        valor_unitario = float(match.group(4).replace(',', '.'))
                        valor_total = float(match.group(5).replace(',', '.'))
                        total_operacao += valor_total
                        total_geral += valor_total
                    except:
                        valor_unitario = match.group(4)
                        valor_total = match.group(5)
                    
                    operacao_item = {
                        'descricao': f"{match.group(1)} - {match.group(2).strip()}",
                        'qtd': match.group(3),
                        'rs_unitario': valor_unitario,
                        'total_oper_rs': valor_total
                    }
                    result['operacao_servicos']['fields'].append(operacao_item)
            
            current_line += 1
        
        result['operacao_servicos']['total_operacao_servicos'] = total_operacao
        total_armazenagem = result['armazenagem']['total_armazenagem_periodos']
        result['operacao_servicos']['total_geral'] = total_armazenagem + total_operacao

    def clean_prefixes(self, data):
        """Remove prefixos indesejados dos campos"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and value.startswith(':'):
                    data[key] = value[1:]
                elif isinstance(value, str) and value.endswith(' IM:'):
                    data[key] = value[:-4]
                elif isinstance(value, (dict, list)):
                    self.clean_prefixes(value)
        elif isinstance(data, list):
            for item in data:
                self.clean_prefixes(item)

    def normalize_string(self, text):
        """Normaliza string removendo espaços extras e normalizando caracteres"""
        if text is None:
            return ''
        normalized = re.sub(r'\s+', ' ', text.strip())
        normalized = re.sub(r'\s+\(', '(', normalized)
        normalized = re.sub(r'\)\s+', ')', normalized)
        return normalized
    
    def normalize_number(self, value):
        """Normaliza números para formato consistente"""
        if isinstance(value, str):
            if ',' in value and '.' in value:
                value = value.replace('.', '').replace(',', '.')
            elif ',' in value and '.' not in value:
                value = value.replace(',', '.')
            return value
        return value

    def round_decimal(self, value, places=2):
        """Arredonda valores decimais para evitar problemas de precisão"""
        if isinstance(value, (int, float)):
            return round(value, places)
        return value

def analyze_pdf(pdf_path):
    """Função principal para análise do PDF"""
    parser = PDFLineParser()
    return parser.parse_pdf(pdf_path) 