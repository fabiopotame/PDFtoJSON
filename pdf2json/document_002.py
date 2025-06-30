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
        """Extrai texto do PDF linha a linha"""
        lines = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines.extend([line.strip() for line in text.split('\n') if line.strip()])
        return lines

    def extract_field_value(self, line_text, field_config):
        """Extrai valor de um campo específico da linha"""
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
        """Valida se o ref_cliente não faz parte do doc_aduan_de_entrada"""
        if ref_value.startswith('NVT '):
            ref_value = ref_value[4:]
        
        if re.match(r'^\d{1,3}$', ref_value):
            if 'doc_aduan_de_entrada' in lote_section:
                doc_entrada = lote_section['doc_aduan_de_entrada']
                if doc_entrada and doc_entrada.endswith(f" - {ref_value}"):
                    return None
        return ref_value

    def _extract_ref_cliente(self, lines, ref_line, lote_section):
        """Extrai dados do ref_cliente"""
        if ref_line is None:
            return None
        
        ref_text = lines[ref_line]
        
        if re.search(r'Ref\.Cliente:\s*$', ref_text):
            # Busca na linha seguinte
            if ref_line + 1 < len(lines):
                next_line = lines[ref_line + 1]
                if next_line:
                    parts = next_line.split(' - ')
                    if len(parts) > 1:
                        return self._validate_ref_cliente(parts[-1].strip(), lote_section)
                    else:
                        # Fallback com regex
                        ref_cliente_match = re.search(r'([A-Z0-9]+(?:[,\-][A-Z0-9]+)*)\s*$', next_line)
                        if ref_cliente_match:
                            return self._validate_ref_cliente(ref_cliente_match.group(1), lote_section)
        else:
            # Valor na mesma linha
            ref_match = re.search(r'Ref\.Cliente:\s*([A-Z0-9\s,.-]+)', ref_text)
            if ref_match:
                ref_value = ref_match.group(1).strip()
                return ref_value if ref_value else None
        
        return None

    def _find_line_indices(self, lines):
        """Encontra índices das linhas importantes"""
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
        """Extrai dados da linha do lote"""
        # Número do lote
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
        
        # Documento aduaneiro de entrada
        doc_entrada_match = re.search(r'([A-Z]{3}\s*-\s*\d{2}/\d+)\s*-\s*([A-Z0-9]+)', lote_text)
        if doc_entrada_match:
            lote_section['doc_aduan_de_entrada'] = f"{doc_entrada_match.group(1)} - {doc_entrada_match.group(2)}"

    def _extract_doc_aduaneiro_data(self, doc_text, lote_section):
        """Extrai dados do documento aduaneiro"""
        # Documento aduaneiro
        doc_match = re.search(r'DI\s+-\s+(\d{4}/\d+)', doc_text)
        if doc_match:
            lote_section['doc_aduaneiro_i'] = f"DI - {doc_match.group(1)}"
        
        # Data de entrada e quantidade de container
        data_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(\d+)', doc_text)
        if data_match:
            lote_section['data_entrada'] = data_match.group(1)
            lote_section['qtd_container'] = data_match.group(2)

    def _extract_valores_data(self, valores_text, lote_section):
        """Extrai dados da linha de valores"""
        # Valores FOB/CIF
        valores_match = re.search(r'(\d+\.\d+,\d+)\s+(\d+\.\d+,\d+)', valores_text)
        if valores_match:
            lote_section['valor_fob_cif_rs'] = float(valores_match.group(1).replace('.', '').replace(',', '.'))
            lote_section['valor_fob_cif_us'] = float(valores_match.group(2).replace('.', '').replace(',', '.'))
        
        # Quantidade do lote
        qtd_match = re.search(r'(\d+\.\d+,\d+)\s+(\d+\.\d+,\d+)\s+(\d+\.\d{2})', valores_text)
        if qtd_match:
            lote_section['qtd_lote'] = qtd_match.group(3)
        
        # Datas de período
        datas_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})', valores_text)
        if datas_match:
            lote_section['periodos_apuracao'] = f"{datas_match.group(1)} a {datas_match.group(2)}"
            lote_section['fim_periodo_armaz'] = datas_match.group(2)
            lote_section['prazo_p_retirada'] = datas_match.group(2)

    def _search_additional_data(self, lines, valores_line, lote_section):
        """Busca dados adicionais nas próximas linhas e no documento"""
        # Busca nas próximas 5 linhas
        for offset in range(1, 6):
            idx = valores_line + offset
            if idx >= len(lines):
                break
            
            line = lines[idx]
            
            # Datas de período
            datas_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})', line)
            if datas_match:
                lote_section['periodos_apuracao'] = f"{datas_match.group(1)} a {datas_match.group(2)}"
                lote_section['fim_periodo_armaz'] = datas_match.group(2)
                lote_section['prazo_p_retirada'] = datas_match.group(2)
            
            # Dias
            dias_match = re.search(r'Dias:\s*(\d+)', line)
            if dias_match:
                lote_section['dias'] = dias_match.group(1)
            
            # Períodos de armazenagem
            periodos_match = re.search(r'Perío[^:]*:\s*(\d+)', line)
            if periodos_match:
                lote_section['periodos_armaz'] = periodos_match.group(1)
        
        # Busca ampliada se não encontrou
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
        """Calcula dias baseado nas datas de período"""
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
        """Parse principal do PDF"""
        lines = self.extract_text_by_lines(pdf_path)
        
        # Inicializa resultado
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
        
        # Processa campos mapeados
        for line_num, field_configs in self.field_mapping.items():
            if line_num <= len(lines):
                line_text = lines[line_num - 1]
                
                for field_name, config in field_configs.items():
                    value = self.extract_field_value(line_text, config)
                    if value:
                        self.set_nested_value(result, field_name, value)
        
        # Processa tabelas dinâmicas
        self.parse_dynamic_tables(lines, result)
        
        # Processa seção do lote
        lote_section = {}
        line_indices = self._find_line_indices(lines)
        
        # Extrai dados do lote
        if line_indices.get('lote') is not None:
            self._extract_lote_data(lines[line_indices['lote']], lote_section)
        
        # Extrai documento aduaneiro
        if line_indices.get('doc_aduaneiro') is not None:
            self._extract_doc_aduaneiro_data(lines[line_indices['doc_aduaneiro']], lote_section)
        
        # Extrai ref_cliente
        lote_section['ref_cliente'] = self._extract_ref_cliente(lines, line_indices.get('ref'), lote_section)
        
        # Extrai valores
        if line_indices.get('valores') is not None:
            self._extract_valores_data(lines[line_indices['valores']], lote_section)
            self._search_additional_data(lines, line_indices['valores'], lote_section)
        
        # Calcula campos derivados
        self._calculate_dias(lote_section)
        
        # Define valores padrão
        lote_section.setdefault('doc_aduaneiro_ii', '')
        lote_section.setdefault('bl_awb_ctrc', None)
        
        # Define períodos de armazenagem baseado na tabela
        if 'armazenagem' in result and 'fields' in result['armazenagem']:
            periodos = len(result['armazenagem']['fields'])
            lote_section['periodos_armaz'] = str(periodos)
        else:
            lote_section['periodos_armaz'] = None
        
        result['informacoes do lote'] = lote_section
        
        # Finaliza resultado
        self.clean_prefixes(result)
        self._normalize_fields(result)
        self._round_totals(result)
        
        # Adiciona campos padrão
        if 'faturar para' in result:
            result['faturar para']['im'] = None
        
        return result

    def _normalize_fields(self, result):
        """Normaliza campos específicos"""
        # Normaliza descrições de operações
        if 'operacao_servicos' in result and 'fields' in result['operacao_servicos']:
            for field in result['operacao_servicos']['fields']:
                if 'descricao' in field:
                    field['descricao'] = self.normalize_string(field['descricao'])
        
        # Normaliza porcentagens de armazenagem
        if 'armazenagem' in result and 'fields' in result['armazenagem']:
            for field in result['armazenagem']['fields']:
                if '%_armaz' in field:
                    field['%_armaz'] = self.normalize_number(field['%_armaz'])

    def _round_totals(self, result):
        """Arredonda totais das operações"""
        if 'operacao_servicos' in result:
            if 'total_geral' in result['operacao_servicos']:
                result['operacao_servicos']['total_geral'] = self.round_decimal(result['operacao_servicos']['total_geral'])
            if 'total_operacao_servicos' in result['operacao_servicos']:
                result['operacao_servicos']['total_operacao_servicos'] = self.round_decimal(result['operacao_servicos']['total_operacao_servicos'])

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
        if 'armazenagem' not in result:
            result['armazenagem'] = {'fields': [], 'total_armazenagem_periodos': 0}
        current_line = start_line + 1
        total_armazenagem = 0.0
        while current_line < len(lines):
            line = lines[current_line]
            if 'TOTAL ARMADOS' in line or 'TOTAL GERAL' in line or 'O P E R A Ç Ã O' in line:
                # Extrai o total da linha se presente
                match = re.search(r'(\d+[\.,]\d+)$', line)
                if match:
                    total_armazenagem = float(match.group(1).replace(',', '.'))
                break
            if line.strip() and not line.startswith('Período'):
                parts = line.split()
                if len(parts) >= 8:
                    try:
                        valor = float(parts[7].replace(',', '.'))
                    except:
                        valor = parts[7]
                    armazenagem_item = {
                        'inicio': parts[0],
                        'final': parts[1],
                        'periodo': parts[2],
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
        if 'operacao_servicos' not in result:
            result['operacao_servicos'] = {'fields': [], 'total_operacao_servicos': 0, 'total_geral': 0}
        current_line = start_line + 1
        total_operacao = 0.0
        total_geral = None
        while current_line < len(lines):
            line = lines[current_line]
            if 'TOTAL GERAL' in line or 'O B S E R V A Ç' in line:
                match = re.search(r'(\d+[\.,]\d+)$', line)
                if match:
                    total_geral = float(match.group(1).replace(',', '.'))
                break
            if line.strip() and not line.startswith('Descrição'):
                # Regex para capturar: código - descrição ... qtd rs_unitario total_oper_rs
                match = re.match(r'^(\d+\s*-\s*.+?)\s+(\d+\.\d+)\s+([\d,.]+)\s+([\d,.]+)$', line)
                if match:
                    descricao = match.group(1).strip()
                    qtd = match.group(2)
                    rs_unitario = float(match.group(3).replace(',', '.'))
                    total_oper_rs = float(match.group(4).replace(',', '.'))
                    operacao_item = {
                        'descricao': descricao,
                        'qtd': qtd,
                        'rs_unitario': rs_unitario,
                        'total_oper_rs': total_oper_rs
                    }
                    result['operacao_servicos']['fields'].append(operacao_item)
            current_line += 1
        result['operacao_servicos']['total_operacao_servicos'] = sum([f['total_oper_rs'] for f in result['operacao_servicos']['fields']])
        if total_geral is not None:
            result['operacao_servicos']['total_geral'] = total_geral
        else:
            result['operacao_servicos']['total_geral'] = result.get('armazenagem', {}).get('total_armazenagem_periodos', 0) + result['operacao_servicos']['total_operacao_servicos']

    def clean_prefixes(self, data):
        """Remove prefixos indesejados dos campos"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    if value.startswith(':'):
                        data[key] = value[1:]
                    elif value.endswith(' IM:'):
                        data[key] = value[:-4]
                elif isinstance(value, (dict, list)):
                    self.clean_prefixes(value)
        elif isinstance(data, list):
            for item in data:
                self.clean_prefixes(item)

    def normalize_string(self, text):
        """Normaliza string removendo espaços extras"""
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

    def round_decimal(self, value, places=2):
        """Arredonda valores decimais"""
        if isinstance(value, (int, float)):
            return round(value, places)
        return value

def analyze_pdf(pdf_path):
    """Função principal para análise do PDF"""
    parser = PDFLineParser()
    return parser.parse_pdf(pdf_path) 