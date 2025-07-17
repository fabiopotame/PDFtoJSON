#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser Baseado em Linhas Fixas - Extrai campos diretamente pelas linhas do PDF
"""

import re
from datetime import datetime
import pdfplumber

class PDFLineParser:
    def __init__(self):
        # Field mapping configuration for line-based extraction
        self.field_mapping = {
            1: {
                'document_type': {'start': 'DEMONSTRATIVO DE CÁLCULO', 'end': None}
            },
            2: {
                'capa': {'start': 'CAPA:', 'end': 'DEMONSTRATIVO:'},
                'demonstrativo': {'start': 'DEMONSTRATIVO:', 'end': 'NOTA FISCAL:'},
                'nota_fiscal': {'start': 'NOTA FISCAL:', 'end': None}
            },
            3: {
                'regime': {'start': 'Regime:', 'end': None}
            },
            4: {
                'tarifa_01': {'start': 'Tarifa 01:', 'end': 'Opção tarifa:'},
                'opcao_tarifa': {'start': 'Opção tarifa:', 'end': None}
            },
            7: {
                'codigo_beneficiario': {'start': 'Código:', 'end': 'Nome:'},
                'nome_beneficiario': {'start': 'Nome:', 'end': 'CNPJ/CPF:'},
                'cnpj_beneficiario': {'start': 'CNPJ/CPF:', 'end': None}
            },
            9: {
                'codigo_comissaria': {'start': 'Código:', 'end': 'Nome:'},
                'nome_comissaria': {'start': 'Nome:', 'end': 'CNPJ/CPF:'},
                'cnpj_comissaria': {'start': 'CNPJ/CPF:', 'end': None}
            },
            11: {
                'codigo_cliente': {'start': 'Código:', 'end': 'Nome:'},
                'nome_cliente': {'start': 'Nome:', 'end': 'Endereço:'},
                'endereco_cliente': {'start': 'Endereço:', 'end': 'Bairro:'},
                'bairro_cliente': {'start': 'Bairro:', 'end': 'Cidade:'},
                'cidade_cliente': {'start': 'Cidade:', 'end': 'Estado:'},
                'estado_cliente': {'start': 'Estado:', 'end': 'CEP:'},
                'cep_cliente': {'start': 'CEP:', 'end': 'CNPJ/CPF:'},
                'cnpj_cliente': {'start': 'CNPJ/CPF:', 'end': 'IE:'},
                'ie_cliente': {'start': 'IE:', 'end': None}
            },
            16: {
                'codigo_faturar': {'start': 'Código:', 'end': 'Nome:'},
                'nome_faturar': {'start': 'Nome:', 'end': 'Endereço:'},
                'endereco_faturar': {'start': 'Endereço:', 'end': 'Bairro:'},
                'bairro_faturar': {'start': 'Bairro:', 'end': 'Cidade:'},
                'cidade_faturar': {'start': 'Cidade:', 'end': 'Estado:'},
                'estado_faturar': {'start': 'Estado:', 'end': 'CEP:'},
                'cep_faturar': {'start': 'CEP:', 'end': 'CNPJ/CPF:'},
                'cnpj_faturar': {'start': 'CNPJ/CPF:', 'end': 'IE:'},
                'ie_faturar': {'start': 'IE:', 'end': None}
            },
            21: {
                'moeda': {'start': 'Moeda:', 'end': 'Data/Cotação:'},
                'data_cotacao': {'start': 'Data/Cotação:', 'end': 'Valor:'},
                'valor_cotacao': {'start': 'Valor:', 'end': None}
            }
        }

    def extract_text_by_lines(self, pdf_path):
        """Extract text from PDF and return as list of lines"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                all_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
                
                lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                return lines
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return []

    def extract_field_value(self, line_text, field_config):
        """Extract field value from line based on configuration"""
        start_marker = field_config.get('start')
        end_marker = field_config.get('end')
        
        if not start_marker:
            return ''
        
        start_pos = line_text.find(start_marker)
        if start_pos == -1:
            return ''
        
        start_pos += len(start_marker)
        
        if end_marker:
            end_pos = line_text.find(end_marker, start_pos)
            if end_pos == -1:
                return line_text[start_pos:].strip()
            return line_text[start_pos:end_pos].strip()
        else:
            return line_text[start_pos:].strip()

    def _validate_ref_cliente(self, ref_value, lote_section):
        """Validate and clean ref_cliente value"""
        if not ref_value:
            return None
        
        # Remove NVT prefix if present
        if ref_value.startswith('NVT '):
            ref_value = ref_value[4:]
        
        # Check if it's part of doc_aduan_de_entrada
        if 'doc_aduan_de_entrada' in lote_section:
            if ref_value in lote_section['doc_aduan_de_entrada']:
                return None
        
        return ref_value

    def _extract_ref_cliente(self, lines, ref_line, lote_section):
        """Extract ref_cliente from lines"""
        if ref_line is None:
            return None
        
        ref_text = lines[ref_line]
        ref_match = re.search(r'Ref\.Cliente:\s*([A-Z0-9]+)', ref_text)
        
        if ref_match:
            ref_value = ref_match.group(1)
            return self._validate_ref_cliente(ref_value, lote_section)
        
        return None

    def _find_line_indices(self, lines):
        """Find important line indices in the document"""
        indices = {}
        
        for i, line in enumerate(lines):
            # Lot line pattern
            if re.match(r'^\d{12}\s+[A-Z]{4,5}\d{8,10}', line):
                indices['lote'] = i
            
            # Customs document line pattern
            elif re.match(r'^DI\s+-\s+\d{4}/\d+', line):
                indices['doc_aduaneiro'] = i
            
            # Values line pattern
            elif re.match(r'^\d+\.\d+,\d+\s+\d+\.\d+,\d+', line):
                indices['valores'] = i
            
            # Reference line pattern
            elif 'Ref.Cliente:' in line:
                indices['ref'] = i
        
        return indices

    def _extract_lote_data(self, lote_text, lote_section):
        """Extract data from lot line"""
        # Lot number
        lote_match = re.match(r'^(\d{12})', lote_text)
        if lote_match:
            lote_section['lote'] = lote_match.group(1)
        
        # BL/AWB/CTRC
        parts = lote_text.split()
        if len(parts) >= 2:
            candidate = parts[1]
            lote_section['bl_awb_ctrc'] = candidate if re.match(r'^[A-Z]{4,5}\d{8,10}$', candidate) else None
        else:
            lote_section['bl_awb_ctrc'] = None
        
        # Customs entry document
        doc_entrada_match = re.search(r'([A-Z]{3}\s*-\s*\d{2}/\d+)\s*-\s*([A-Z0-9]+)', lote_text)
        if doc_entrada_match:
            lote_section['doc_aduan_de_entrada'] = f"{doc_entrada_match.group(1)} - {doc_entrada_match.group(2)}"

    def _extract_doc_aduaneiro_data(self, doc_text, lote_section):
        """Extract data from customs document"""
        # Customs document
        doc_match = re.search(r'DI\s+-\s+(\d{4}/\d+)', doc_text)
        if doc_match:
            lote_section['doc_aduaneiro_i'] = f"DI - {doc_match.group(1)}"
        
        # Entry date and container quantity
        data_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(\d+)', doc_text)
        if data_match:
            lote_section['data_entrada'] = data_match.group(1)
            lote_section['qtd_container'] = data_match.group(2)

    def _extract_valores_data(self, valores_text, lote_section):
        """Extract data from values line"""
        # FOB/CIF values
        valores_match = re.search(r'(\d+\.\d+,\d+)\s+(\d+\.\d+,\d+)', valores_text)
        if valores_match:
            lote_section['valor_fob_cif_rs'] = float(valores_match.group(1).replace('.', '').replace(',', '.'))
            lote_section['valor_fob_cif_us'] = float(valores_match.group(2).replace('.', '').replace(',', '.'))
        
        # Lot quantity
        qtd_match = re.search(r'(\d+\.\d+,\d+)\s+(\d+\.\d+,\d+)\s+(\d+\.\d{2})', valores_text)
        if qtd_match:
            lote_section['qtd_lote'] = qtd_match.group(3)
        
        # Period dates
        datas_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})', valores_text)
        if datas_match:
            lote_section['periodos_apuracao'] = f"{datas_match.group(1)} a {datas_match.group(2)}"
            lote_section['fim_periodo_armaz'] = datas_match.group(2)
            lote_section['prazo_p_retirada'] = datas_match.group(2)

    def _search_additional_data(self, lines, valores_line, lote_section):
        """Search for additional data in next lines and document"""
        # Search in next 5 lines
        for offset in range(1, 6):
            idx = valores_line + offset
            if idx >= len(lines):
                break
            
            line = lines[idx]
            
            # Period dates
            datas_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})', line)
            if datas_match:
                lote_section['periodos_apuracao'] = f"{datas_match.group(1)} a {datas_match.group(2)}"
                lote_section['fim_periodo_armaz'] = datas_match.group(2)
                lote_section['prazo_p_retirada'] = datas_match.group(2)
            
            # Days
            dias_match = re.search(r'Dias:\s*(\d+)', line)
            if dias_match:
                lote_section['dias'] = dias_match.group(1)
            
            # Storage periods
            periodos_match = re.search(r'Perío[^:]*:\s*(\d+)', line)
            if periodos_match:
                lote_section['periodos_armaz'] = periodos_match.group(1)
        
        # Extended search if not found
        if 'dias' not in lote_section:
            for line in lines:
                if 'Dias:' in line:
                    dias_match = re.search(r'Dias:\s*(\d+)', line)
                    if dias_match:
                        lote_section['dias'] = dias_match.group(1)
                        break
        
        if 'periodos_armaz' not in lote_section:
            for line in lines:
                if 'Perío' in line and ':' in line:
                    periodos_match = re.search(r'Perío[^:]*:\s*(\d+)', line)
                    if periodos_match:
                        lote_section['periodos_armaz'] = periodos_match.group(1)
                        break

    def _calculate_dias(self, lote_section):
        """Calculate days based on period dates"""
        if 'periodos_apuracao' in lote_section:
            try:
                datas_text = lote_section['periodos_apuracao']
                datas_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})', datas_text)
                if datas_match:
                    data_inicio = datetime.strptime(datas_match.group(1), '%d/%m/%Y')
                    data_fim = datetime.strptime(datas_match.group(2), '%d/%m/%Y')
                    dias = (data_fim - data_inicio).days + 1
                    lote_section['dias'] = str(dias)
            except Exception:
                lote_section['dias'] = None

    def parse_pdf(self, pdf_path):
        """Main PDF parser"""
        lines = self.extract_text_by_lines(pdf_path)
        
        # Initialize result
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
        
        # Process mapped fields
        for line_num, field_configs in self.field_mapping.items():
            if line_num <= len(lines):
                line_text = lines[line_num - 1]
                
                for field_name, config in field_configs.items():
                    value = self.extract_field_value(line_text, config)
                    if value:
                        self.set_nested_value(result, field_name, value)
        
        # Process dynamic tables
        self.parse_dynamic_tables(lines, result)
        
        # Process lot section
        lote_section = {}
        line_indices = self._find_line_indices(lines)
        
        # Extract lot data
        if line_indices.get('lote') is not None:
            self._extract_lote_data(lines[line_indices['lote']], lote_section)
        
        # Extract customs document
        if line_indices.get('doc_aduaneiro') is not None:
            self._extract_doc_aduaneiro_data(lines[line_indices['doc_aduaneiro']], lote_section)
        
        # Extract ref_cliente
        lote_section['ref_cliente'] = self._extract_ref_cliente(lines, line_indices.get('ref'), lote_section)
        
        # Extract values
        if line_indices.get('valores') is not None:
            self._extract_valores_data(lines[line_indices['valores']], lote_section)
            self._search_additional_data(lines, line_indices['valores'], lote_section)
        
        # Calculate derived fields
        self._calculate_dias(lote_section)
        
        # Set default values
        lote_section.setdefault('doc_aduaneiro_ii', '')
        lote_section.setdefault('bl_awb_ctrc', None)
        
        # Set storage periods based on table
        if 'armazenagem' in result and 'fields' in result['armazenagem']:
            periodos = len(result['armazenagem']['fields'])
            lote_section['periodos_armaz'] = str(periodos)
        else:
            lote_section['periodos_armaz'] = None
        
        result['informacoes do lote'] = lote_section
        
        # Finalize result
        self.clean_prefixes(result)
        self._normalize_fields(result)
        self._round_totals(result)
        
        # Add default fields
        if 'faturar para' in result:
            result['faturar para']['im'] = None
        
        return result

    def _normalize_fields(self, result):
        """Normalize specific fields"""
        # Normalize operation descriptions
        if 'operacao_servicos' in result and 'fields' in result['operacao_servicos']:
            for field in result['operacao_servicos']['fields']:
                if 'descricao' in field:
                    field['descricao'] = self.normalize_string(field['descricao'])
        
        # Normalize storage percentages
        if 'armazenagem' in result and 'fields' in result['armazenagem']:
            for field in result['armazenagem']['fields']:
                if 'percentual' in field:
                    field['percentual'] = self.normalize_number(field['percentual'])

    def _round_totals(self, result):
        """Round total values"""
        if 'armazenagem' in result:
            result['armazenagem']['total_armazenagem_periodos'] = self.round_decimal(
                result['armazenagem']['total_armazenagem_periodos']
            )
        
        if 'operacao_servicos' in result:
            result['operacao_servicos']['total_operacao_servicos'] = self.round_decimal(
                result['operacao_servicos']['total_operacao_servicos']
            )
            result['operacao_servicos']['total_geral'] = self.round_decimal(
                result['operacao_servicos']['total_geral']
            )

    def set_nested_value(self, data, field_path, value):
        """Set nested value in data structure"""
        keys = field_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value

    def parse_dynamic_tables(self, lines, result):
        """Parse dynamic tables in the document"""
        for i, line in enumerate(lines):
            if 'ARMAZENAGEM' in line and 'PERÍODOS' in line:
                self.parse_armazenagem_table(lines, i, result)
            elif 'OPERAÇÃO' in line and 'SERVIÇOS' in line:
                self.parse_operacao_table(lines, i, result)

    def parse_armazenagem_table(self, lines, start_line, result):
        """Parse storage table"""
        fields = []
        current_line = start_line + 1
        
        while current_line < len(lines):
            line = lines[current_line]
            
            # Check for table end
            if 'TOTAL ARMAZENAGEM' in line or 'OPERAÇÃO' in line:
                break
            
            # Parse table row
            if re.match(r'^\d+', line):
                parts = line.split()
                if len(parts) >= 4:
                    field = {
                        'periodo': parts[0],
                        'dias': parts[1],
                        'percentual': self.normalize_number(parts[2]),
                        'valor': self.normalize_number(parts[3])
                    }
                    fields.append(field)
            
            current_line += 1
        
        result['armazenagem']['fields'] = fields
        result['armazenagem']['total_armazenagem_periodos'] = sum(
            field['valor'] for field in fields
        )

    def parse_operacao_table(self, lines, start_line, result):
        """Parse operation table"""
        fields = []
        current_line = start_line + 1
        
        while current_line < len(lines):
            line = lines[current_line]
            
            # Check for table end
            if 'TOTAL OPERAÇÃO' in line or 'TOTAL GERAL' in line:
                break
            
            # Parse table row using regex
            # Regex to capture: code - description ... qty unit_price total_operation_rs
            match = re.match(r'^(\d+)\s*-\s*(.+?)\s+(\d+)\s+([\d,]+)\s+([\d,]+)', line)
            if match:
                field = {
                    'codigo': match.group(1),
                    'descricao': self.normalize_string(match.group(2)),
                    'quantidade': int(match.group(3)),
                    'valor_unitario': self.normalize_number(match.group(4)),
                    'total_operacao_rs': self.normalize_number(match.group(5))
                }
                fields.append(field)
            
            current_line += 1
        
        result['operacao_servicos']['fields'] = fields
        result['operacao_servicos']['total_operacao_servicos'] = sum(
            field['total_operacao_rs'] for field in fields
        )
        
        # Calculate total geral
        armazenagem_total = result['armazenagem']['total_armazenagem_periodos']
        operacao_total = result['operacao_servicos']['total_operacao_servicos']
        result['operacao_servicos']['total_geral'] = armazenagem_total + operacao_total

    def clean_prefixes(self, data):
        """Clean prefixes from field values"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    # Remove common prefixes
                    prefixes_to_remove = ['Código:', 'Nome:', 'CNPJ/CPF:', 'Endereço:', 'Bairro:', 'Cidade:', 'Estado:', 'CEP:', 'IE:']
                    for prefix in prefixes_to_remove:
                        if value.startswith(prefix):
                            value = value[len(prefix):].strip()
                            data[key] = value
                elif isinstance(value, dict):
                    self.clean_prefixes(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            self.clean_prefixes(item)

    def normalize_string(self, text):
        """Normalize string by removing extra spaces and special characters"""
        if not text:
            return text
        return ' '.join(text.split())

    def normalize_number(self, value):
        """Normalize number by converting string to float"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove currency symbols and convert comma to dot
            value = value.replace('R$', '').replace('$', '').replace(' ', '')
            # Se houver apenas uma vírgula e nenhum ponto, é decimal brasileiro
            if value.count(',') == 1 and value.count('.') == 0:
                value = value.replace(',', '.')
            # Se houver ponto como separador de milhar e vírgula como decimal
            elif value.count('.') > 0 and value.count(',') == 1:
                value = value.replace('.', '').replace(',', '.')
            try:
                return float(value)
            except ValueError:
                return 0.0
        return 0.0

    def round_decimal(self, value, places=2):
        """Round decimal value to specified places"""
        try:
            return round(float(value), places)
        except (ValueError, TypeError):
            return 0.0

def analyze_pdf(pdf_path):
    """Main function to analyze PDF"""
    parser = PDFLineParser()
    return parser.parse_pdf(pdf_path) 