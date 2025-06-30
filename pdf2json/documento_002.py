import re
from datetime import datetime
import pdfplumber

#Documento DEMONSTRATIVO DE CÁLCULO

class PDFLineParser:
    def __init__(self):
        self.field_mapping = {
            2: {
                'header.capa': {'start': 'CAPA:', 'end': 'DEMONSTRATIVO:'},
                'header.demonstrativo': {'start': 'DEMONSTRATIVO:', 'end': 'NOTA FISCAL:'},
                'header.nota_fiscal': {'start': 'NOTA FISCAL:', 'end': None}
            },
            3: {'header.regime': {'start': 'Regime:', 'end': None}},
            4: {'header.tarifa 01': {'start': 'Tarifa 01:', 'end': None}},
            5: {'header.opcao_tarifa': {'start': 'Opção tarifa:', 'end': None}},
            7: {
                'beneficiario.codigo': {'start': 'Código:', 'end': 'Nome:'},
                'beneficiario.nome': {'start': 'Nome:', 'end': 'CNPJ/CPF:'},
                'beneficiario.cnpj_cpf': {'start': 'CNPJ/CPF:', 'end': None}
            },
            9: {
                'comissaria.codigo': {'start': 'Código:', 'end': 'Nome:'},
                'comissaria.nome': {'start': 'Nome:', 'end': 'CNPJ/CPF:'},
                'comissaria.cnpj_cpf': {'start': 'CNPJ/CPF:', 'end': None}
            },
            11: {
                'cliente.codigo': {'start': 'Código:', 'end': 'Nome:'},
                'cliente.nome': {'start': 'Nome:', 'end': None}
            },
            12: {'cliente.endereco': {'start': 'Endereço:', 'end': None}},
            13: {
                'cliente.bairro': {'start': 'Bairro:', 'end': 'Cidade:'},
                'cliente.cidade': {'start': 'Cidade:', 'end': 'Estado:'},
                'cliente.estado': {'start': 'Estado:', 'end': 'CEP:'},
                'cliente.cep': {'start': 'CEP:', 'end': None}
            },
            14: {
                'cliente.cnpj_cpf': {'start': 'CNPJ/CPF:', 'end': 'IE:'},
                'cliente.ie': {'start': 'IE:', 'end': None}
            },
            16: {
                'faturar para.codigo': {'start': 'Código:', 'end': 'Nome:'},
                'faturar para.nome': {'start': 'Nome:', 'end': None}
            },
            17: {'faturar para.endereco': {'start': 'Endereço:', 'end': None}},
            18: {
                'faturar para.bairro': {'start': 'Bairro:', 'end': 'Cidade:'},
                'faturar para.cidade': {'start': 'Cidade:', 'end': 'Estado:'},
                'faturar para.estado': {'start': 'Estado:', 'end': 'CEP:'},
                'faturar para.cep': {'start': 'CEP:', 'end': None}
            },
            19: {
                'faturar para.cnpj_cpf': {'start': 'CNPJ/CPF:', 'end': 'IE:'},
                'faturar para.ie': {'start': 'IE:', 'end': None}
            },
            21: {
                'tarifas aplicadas.moeda': {'start': 'Moeda:', 'end': 'Data/Cotação:'},
                'tarifas aplicadas.cotacao': {'start': 'Data/Cotação:', 'end': 'Valor:'},
                'tarifas aplicadas.valor_cotacao': {'start': 'Valor:', 'end': None}
            }
        }

    def extract_text_by_lines(self, pdf_path):
        """Extracts text from PDF line by line"""
        lines = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines.extend([line.strip() for line in text.split('\n') if line.strip()])
        return lines

    def extract_field_value(self, line_text, field_config):
        """Extracts value from a specific field in the line"""
        if not line_text:
            return ""
        
        start_marker = field_config['start']
        end_marker = field_config['end']
        
        if start_marker is None:
            return line_text.strip()
        
        start_pos = line_text.find(start_marker)
        if start_pos == -1:
            return ""
        
        value_start = start_pos + len(start_marker)
        
        if end_marker is None:
            return line_text[value_start:].strip()
        
        end_pos = line_text.find(end_marker, value_start)
        if end_pos == -1:
            return line_text[value_start:].strip()
        
        return line_text[value_start:end_pos].strip()

    def _validate_ref_cliente(self, ref_value, lote_section):
        """Validates if ref_cliente is not part of doc_aduan_de_entrada"""
        if ref_value.startswith('NVT '):
            ref_value = ref_value[4:]
        
        if re.match(r'^\d{1,3}$', ref_value):
            if 'doc_aduan_de_entrada' in lote_section:
                doc_entrada = lote_section['doc_aduan_de_entrada']
                if doc_entrada and doc_entrada.endswith(f" - {ref_value}"):
                    return None
        return ref_value

    def _extract_ref_cliente(self, lines, ref_line, lote_section):
        """Extracts ref_cliente data"""
        if ref_line is None:
            return None
        
        ref_text = lines[ref_line]
        
        if re.search(r'Ref\.Cliente:\s*$', ref_text):
            # Search in the next line
            if ref_line + 1 < len(lines):
                next_line = lines[ref_line + 1]
                if next_line:
                    parts = next_line.split(' - ')
                    if len(parts) > 1:
                        return self._validate_ref_cliente(parts[-1].strip(), lote_section)
                    else:
                        # Fallback with regex
                        ref_cliente_match = re.search(r'([A-Z0-9]+(?:[,\-][A-Z0-9]+)*)\s*$', next_line)
                        if ref_cliente_match:
                            return self._validate_ref_cliente(ref_cliente_match.group(1), lote_section)
        else:
            # Value in the same line
            ref_match = re.search(r'Ref\.Cliente:\s*([A-Z0-9\s,.-]+)', ref_text)
            if ref_match:
                ref_value = ref_match.group(1).strip()
                return ref_value if ref_value else None
        
        return None

    def _find_line_indices(self, lines):
        """Finds indices of important lines"""
        indices = {}
        
        for i, line in enumerate(lines):
            if re.match(r'^\d{12}\s+\w+', line):
                indices['lote'] = i
            elif re.match(r'^DI\s+-\s+\d{4}/\d+', line):
                indices['doc_aduaneiro'] = i
            elif re.match(r'^\d+\.\d+,\d+\s+\d+\.\d+,\d+', line):
                indices['valores'] = i
            elif 'Ref.Cliente:' in line:
                indices['ref'] = i
        
        return indices

    def _extract_lote_data(self, lote_text, lote_section):
        """Extracts data from the lot line"""
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
        """Extracts customs document data"""
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
        """Extracts data from the values line"""
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
        """Searches for additional data in nearby lines"""
        # Search for withdrawal deadline
        for i in range(valores_line + 1, min(valores_line + 5, len(lines))):
            if i < len(lines):
                line = lines[i]
                prazo_match = re.search(r'Prazo\s+p/\s+retirada:\s*(\d{2}/\d{2}/\d{4})', line)
                if prazo_match:
                    lote_section['prazo_p_retirada'] = prazo_match.group(1)
                    break
        
        # Search for end of storage period
        for i in range(valores_line + 1, min(valores_line + 5, len(lines))):
            if i < len(lines):
                line = lines[i]
                fim_armaz_match = re.search(r'Fim\s+período\s+armaz\.:\s*(\d{2}/\d{2}/\d{4})', line)
                if fim_armaz_match:
                    lote_section['fim_periodo_armaz'] = fim_armaz_match.group(1)
                    break
        
        # Search for storage periods
        for i in range(valores_line + 1, min(valores_line + 5, len(lines))):
            if i < len(lines):
                line = lines[i]
                periodos_match = re.search(r'Períodos\s+armaz\.:\s*(\d+)', line)
                if periodos_match:
                    lote_section['periodos_armaz'] = periodos_match.group(1)
                    break

    def _calculate_dias(self, lote_section):
        """Calculates days based on dates"""
        if 'data_entrada' in lote_section and 'prazo_p_retirada' in lote_section:
            try:
                entrada = datetime.strptime(lote_section['data_entrada'], '%d/%m/%Y')
                prazo = datetime.strptime(lote_section['prazo_p_retirada'], '%d/%m/%Y')
                dias = (prazo - entrada).days
                lote_section['dias'] = str(dias)
            except:
                lote_section['dias'] = None

    def parse_pdf(self, pdf_path):
        """Main function to parse the PDF"""
        lines = self.extract_text_by_lines(pdf_path)
        result = {}
        # Extract fields mapped by line
        for line_num, fields in self.field_mapping.items():
            if line_num < len(lines):
                line_text = lines[line_num]
                for field_path, config in fields.items():
                    value = self.extract_field_value(line_text, config)
                    if value:
                        self.set_nested_value(result, field_path, value)
        # Extract data from "lot information" section
        indices = self._find_line_indices(lines)
        lote_section = {}
        if 'lote' in indices:
            lote_line = lines[indices['lote']]
            self._extract_lote_data(lote_line, lote_section)
        if 'doc_aduaneiro' in indices:
            doc_line = lines[indices['doc_aduaneiro']]
            self._extract_doc_aduaneiro_data(doc_line, lote_section)
        if 'valores' in indices:
            valores_line = lines[indices['valores']]
            self._extract_valores_data(valores_line, lote_section)
            self._search_additional_data(lines, indices['valores'], lote_section)
        if 'ref' in indices:
            ref_cliente = self._extract_ref_cliente(lines, indices['ref'], lote_section)
            if ref_cliente:
                lote_section['ref_cliente'] = ref_cliente
        # Calculate days
        self._calculate_dias(lote_section)
        # Add assessment periods
        if 'data_entrada' in lote_section and 'fim_periodo_armaz' in lote_section:
            lote_section['periodos_apuracao'] = f"{lote_section['data_entrada']} a {lote_section['fim_periodo_armaz']}"
        if lote_section:
            result['informacoes do lote'] = lote_section
        # Parse dynamic tables
        self.parse_dynamic_tables(lines, result)
        # Normalize fields
        self._normalize_fields(result)
        # Adicionar campos vazios apenas se não existirem
        campos_esperados = [
            'header', 'beneficiario', 'comissaria', 'cliente', 'faturar para',
            'tarifas aplicadas', 'informacoes do lote', 'armazenagem', 'operacao_servicos', 'observacoes'
        ]
        for campo in campos_esperados:
            if campo not in result:
                if campo == 'observacoes':
                    result[campo] = ""
                else:
                    result[campo] = {}
        return result

    def _normalize_fields(self, result):
        """Normalizes result fields"""
        # Add missing fields with default values
        if 'faturar para' in result and 'im' not in result['faturar para']:
            result['faturar para']['im'] = None
        
        if 'observacoes' not in result:
            result['observacoes'] = ""

    def _round_totals(self, result):
        """Rounds totals to 2 decimal places"""
        if 'armazenagem' in result and 'total_armazenagem_periodos' in result['armazenagem']:
            result['armazenagem']['total_armazenagem_periodos'] = round(
                result['armazenagem']['total_armazenagem_periodos'], 2
            )
        
        if 'operacao_servicos' in result and 'total_geral' in result['operacao_servicos']:
            result['operacao_servicos']['total_geral'] = round(
                result['operacao_servicos']['total_geral'], 2
            )

    def set_nested_value(self, data, field_path, value):
        """Sets value in nested structure"""
        keys = field_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value

    def parse_dynamic_tables(self, lines, result):
        """Parses dynamic tables (storage and service operations)"""
        for i, line in enumerate(lines):
            if 'ARMADOS' in line or 'Armazenagem' in line:
                self.parse_armazenagem_table(lines, i, result)
            elif 'OPERAÇÃO DE SERVIÇOS' in line:
                self.parse_operacao_table(lines, i, result)

    def parse_armazenagem_table(self, lines, start_line, result):
        """Parses storage table"""
        armazenagem = {'fields': [], 'total_armazenagem_periodos': 0}
        
        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            
            # Check if reached end of table
            if 'TOTAL ARMADOS' in line or 'TOTAL GERAL' in line:
                break
            
            # Extract data from storage line
            if re.match(r'^\d+\.\d+,\d+\s+\d+\.\d+,\d+', line):
                parts = line.split()
                if len(parts) >= 6:
                    field = {
                        'inicio': parts[0],
                        'final': parts[1],
                        'periodo': parts[2],
                        'qtde_pecas': parts[3],
                        'carregado': parts[4],
                        'saldo': parts[5],
                        '%_armaz': parts[6] if len(parts) > 6 else '0',
                        'total_armaz_rs': float(parts[7].replace(',', '.')) if len(parts) > 7 else 0
                    }
                    armazenagem['fields'].append(field)
                    armazenagem['total_armazenagem_periodos'] += field['total_armaz_rs']
        
        if armazenagem['fields']:
            result['armazenagem'] = armazenagem
            self._round_totals(result)

    def parse_operacao_table(self, lines, start_line, result):
        """Parses service operations table"""
        operacao = {'fields': [], 'total_operacao_servicos': 0, 'total_geral': 0}
        
        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            
            # Check if reached end of table
            if 'TOTAL GERAL' in line:
                total_match = re.search(r'(\d+\.\d+,\d+)', line)
                if total_match:
                    operacao['total_geral'] = float(total_match.group(1).replace(',', '.'))
                break
            
            # Extract data from operation line
            if re.match(r'^\d+\s+-\s+', line):
                parts = line.split()
                if len(parts) >= 5:
                    descricao = ' '.join(parts[1:-4])  # Everything between code and values
                    field = {
                        'descricao': f"{parts[0]} - {descricao}",
                        'qtd': parts[-4],
                        'rs_unitario': float(parts[-3].replace(',', '.')),
                        'total_oper_rs': float(parts[-2].replace(',', '.'))
                    }
                    operacao['fields'].append(field)
                    operacao['total_operacao_servicos'] += field['total_oper_rs']
        
        if operacao['fields']:
            result['operacao_servicos'] = operacao
            self._round_totals(result)

    def clean_prefixes(self, data):
        """Removes unnecessary prefixes from fields"""
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                clean_key = key.replace('header.', '').replace('beneficiario.', '').replace('cliente.', '')
                if isinstance(value, dict):
                    cleaned[clean_key] = self.clean_prefixes(value)
                else:
                    cleaned[clean_key] = value
            return cleaned
        return data

    def normalize_string(self, text):
        """Normalizes string by removing extra spaces"""
        if isinstance(text, str):
            return ' '.join(text.split())
        return text

    def normalize_number(self, value):
        """Normalizes number"""
        if isinstance(value, str):
            try:
                return float(value.replace(',', '.'))
            except:
                return value
        return value

    def round_decimal(self, value, places=2):
        """Rounds decimal"""
        if isinstance(value, (int, float)):
            return round(value, places)
        return value

def analyze_pdf(pdf_path):
    """Wrapper function for line-based analysis"""
    parser = PDFLineParser()
    return parser.parse_pdf(pdf_path) 