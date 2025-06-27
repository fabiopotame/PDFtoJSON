import re
import pdfplumber
from PyPDF2 import PdfReader

def extract_text(stream):
    """
    Extract text from PDF using pdfplumber
    """
    with pdfplumber.open(stream) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)

def read_metadata(stream):
    """
    Read PDF metadata using PyPDF2
    """
    reader = PdfReader(stream)
    raw = reader.metadata or {}
    return {k.lstrip('/'): raw[k] for k in raw}

def parse_header_block(text):
    """
    Parse the header block of the PDF document
    Extracts client, CNPJ, vessel, berth, draft, and gross value information
    """
    header = {}
    
    # Extract client information
    m = re.search(r'CLIENTE:\s*(.*?)\s*NAVIO:', text, re.S)
    if m:
        header["Cliente (Customer)"] = m.group(1).strip()
    
    # Extract CNPJ
    m = re.search(r'CNPJ:\s*(\d+)', text)
    if m:
        header["CNPJ (Tax_id)"] = m.group(1)
    
    # Extract vessel information
    m = re.search(r'NAVIO:\s*(.*?)\s+DEMONSTRATIVO:', text, re.S)
    if m:
        header["NAVIO (Vessel)"] = m.group(1).strip()
    
    # Extract berth information
    m = re.search(r'ATRAÇÃO:\s*(.*?)\s', text)
    if m:
        valor = m.group(1).strip()
        if not valor or valor.upper() in ["VALOR", "BRUTO", "R$", "TOTAL"]:
            header["ATRAÇÃO (Berth_ata)"] = None
        else:
            header["ATRAÇÃO (Berth_ata)"] = valor
    else:
        header["ATRAÇÃO (Berth_ata)"] = None
    
    # Extract draft information
    m = re.search(r'DEMONSTRATIVO:\s*(\d+)', text)
    if m:
        header["DEMONSTRATIVO (Draft)"] = m.group(1)
    
    # Extract gross value
    m = re.search(r'VALOR BRUTO R\$:\s*\(BRL\)\s*([\d\.,]+)', text)
    if m:
        valor = m.group(1).replace('.', '').replace(',', '.')
        header["VALOR BRUTO R$: (BRL)"] = float(valor)
    
    return header

def extract_text_with_coordinates(stream):
    """
    Extract text with coordinates for position analysis
    """
    with pdfplumber.open(stream) as pdf:
        all_words = []
        for page_num, page in enumerate(pdf.pages):
            words = page.extract_words()
            for word in words:
                word['page'] = page_num
                all_words.append(word)
        return all_words

def analyze_pdf_structure(stream):
    """
    Analyze the PDF structure line by line to understand the layout.
    Reads from top to bottom, starting from the first page.
    Also captures color information.
    """
    # Extract header first (already works)
    header = parse_header_block(extract_text(stream))
    
    # Extract all words with coordinates, page by page
    all_words = []
    with pdfplumber.open(stream) as pdf:
        for page_num, page in enumerate(pdf.pages):
            words = page.extract_words()
            for word in words:
                word['page'] = page_num
                # Try to extract color information
                try:
                    # Search for characters in the word area to get color info
                    chars = page.chars
                    word_chars = []
                    for char in chars:
                        if (char['x0'] >= word['x0'] and char['x1'] <= word['x1'] and 
                            char['top'] >= word['top'] and char['bottom'] <= word['bottom']):
                            word_chars.append(char)
                    if word_chars:
                        # Check if there is color information
                        colors = set()
                        for char in word_chars:
                            if 'non_stroking_color' in char and char['non_stroking_color']:
                                colors.add(str(char['non_stroking_color']))
                            if 'stroking_color' in char and char['stroking_color']:
                                colors.add(str(char['stroking_color']))
                        if colors:
                            word['colors'] = list(colors)
                        else:
                            word['colors'] = ['black']  # Default
                    else:
                        word['colors'] = ['black']  # Default
                except Exception as e:
                    word['colors'] = ['black']  # Default in case of error
                all_words.append(word)
    # Group words by line (same Y coordinate) within each page
    lines = {}
    for word in all_words:
        # Create a unique key by page and Y coordinate
        y_key = (word['page'], round(word['top'], 1))
        if y_key not in lines:
            lines[y_key] = []
        lines[y_key].append(word)
    # Sort lines by page and then by Y (top to bottom)
    sorted_lines = sorted(lines.items(), key=lambda x: (x[0][0], x[0][1]))
    for i, ((page_num, y), line_words) in enumerate(sorted_lines):
        # Sort words in the line by X (left to right)
        sorted_words = sorted(line_words, key=lambda w: w['x0'])
        # Join line text
        line_text = ' '.join([w['text'] for w in sorted_words])
        # Identify if it is a known section
        known_sections = [
            'Armazenagem Importacao FCL Cheio',
            'Cadastro de BL',
            'Handling - In',
            'Handling - Out',
            'Handling Entre Margem',
            'Presenca de Carga',
            'Repasse Codesp - Tabela III',
            'Scanner'
        ]
        for section in known_sections:
            if section.lower() in line_text.lower():
                break
        # Identify if it is a header line (contains fields)
        if any(field in line_text for field in ['Data Inicial', 'Data Final', 'Container', 'Categoria']):
            pass
        # Identify if it is a value line (contains dates)
        if re.search(r'\d{2}/\d{2}/\d{2}', line_text):
            pass
        # Stop after showing the first 40 lines to avoid overload
        if i >= 39:
            break
    return {
        "header": header,
        "total_lines": len(sorted_lines),
        "lines_analyzed": min(40, len(sorted_lines))
    }

def extract_color_info(stream):
    """
    Extrai informações detalhadas sobre cores e estilos do PDF
    """
    with pdfplumber.open(stream) as pdf:
        for page_num, page in enumerate(pdf.pages):
            chars = page.chars
            
            # Agrupar por cores
            color_groups = {}
            for char in chars:
                color_key = 'black'  # Default
                
                if 'non_stroking_color' in char and char['non_stroking_color']:
                    color_key = str(char['non_stroking_color'])
                elif 'stroking_color' in char and char['stroking_color']:
                    color_key = str(char['stroking_color'])
                
                if color_key not in color_groups:
                    color_groups[color_key] = []
                color_groups[color_key].append(char)
            
            # Mostrar estatísticas de cores
            for color, chars_list in color_groups.items():
                pass
                
            # Extrair linhas com informações de cor
            lines = page.lines
            for i, line in enumerate(lines[:5]):  # Mostrar apenas as primeiras 5 linhas
                pass
            
            # Extrair retângulos (possíveis backgrounds)
            rects = page.rects
            for i, rect in enumerate(rects[:3]):  # Mostrar apenas os primeiros 3
                pass
    
    return {"message": "Análise de cores concluída"}

def extract_sections_by_color_and_coordinates(stream):
    """
    Extrai dados das seções baseada na cor azul (background) e coordenadas específicas
    """
    sections_data = []
    
    with pdfplumber.open(stream) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Extrair linhas e retângulos (backgrounds)
            lines = page.lines
            rects = page.rects
            
            # Extrair caracteres e agrupar por linha
            chars = page.chars
            
            # Agrupar caracteres por linha (mesma coordenada Y)
            char_lines = {}
            for char in chars:
                y_key = round(char['top'], 1)
                if y_key not in char_lines:
                    char_lines[y_key] = []
                char_lines[y_key].append(char)
            
            # Ordenar linhas por Y (de cima para baixo)
            sorted_char_lines = sorted(char_lines.items(), key=lambda x: x[0])
            
            # Para cada linha de caracteres, verificar se há uma linha/retângulo azul na mesma posição
            for y, line_chars in sorted_char_lines:
                # Ordenar caracteres da linha por X (esquerda para direita)
                sorted_chars = sorted(line_chars, key=lambda c: c['x0'])
                
                # Verificar se há uma linha ou retângulo azul nesta posição Y
                background_color = None
                
                # Verificar linhas
                for line in lines:
                    if abs(line['top'] - y) < 5:  # Tolerância de 5 pixels
                        if 'stroking_color' in line and line['stroking_color']:
                            background_color = str(line['stroking_color'])
                            break
                        elif 'non_stroking_color' in line and line['non_stroking_color']:
                            background_color = str(line['non_stroking_color'])
                            break
                
                # Verificar retângulos
                if not background_color:
                    for rect in rects:
                        if abs(rect['top'] - y) < 5:  # Tolerância de 5 pixels
                            if 'non_stroking_color' in rect and rect['non_stroking_color']:
                                background_color = str(rect['non_stroking_color'])
                                break
                            elif 'stroking_color' in rect and rect['stroking_color']:
                                background_color = str(rect['stroking_color'])
                                break
                
                # Verificar se é a cor azul específica
                if background_color == "(0.098, 0.098, 0.439)":
                    # Extrair título da linha azul
                    title_text = ""
                    for char in sorted_chars:
                        if 7.2 <= char['x0'] <= 400:
                            title_text += char['text']
                    title_text = title_text.strip()
                    
                    # Verificar se é uma seção válida
                    if title_text and any(section in title_text for section in [
                        'Armazenagem', 'Cadastro', 'Handling', 'Presenca', 'Repasse', 'Scanner'
                    ]):
                        
                        # Buscar o header das colunas (linha logo abaixo da linha azul)
                        header_columns = {}
                        header_y = None
                        header_english_y = None
                        
                        # Procurar as duas linhas mais próximas abaixo da linha azul
                        for next_y, next_chars in sorted_char_lines:
                            if next_y > y and next_y <= y + 50:  # Dentro de 50 pixels abaixo
                                # Verificar se esta linha contém os nomes das colunas
                                next_text = ''.join([c['text'] for c in sorted(next_chars, key=lambda c: c['x0'])])
                                
                                # Verificar se contém palavras-chave dos headers em português
                                if any(keyword in next_text for keyword in [
                                    'Data Inicial', 'Data Final', 'Container', 'Categoria', 'Armador',
                                    'Manifesto', 'Importador', 'Exportador', 'Observacoes'
                                ]):
                                    header_y = next_y
                                    
                                    # Extrair as palavras e suas coordenadas X da linha em português
                                    sorted_header_chars = sorted(next_chars, key=lambda c: c['x0'])
                                    
                                    # Capturar cada palavra individual com suas coordenadas
                                    words_info = []
                                    current_word = ""
                                    current_x_start = None
                                    current_x_end = None
                                    
                                    for char in sorted_header_chars:
                                        if current_x_start is None:
                                            current_x_start = char['x0']
                                        
                                        # Se é um espaço ou gap grande, finaliza a palavra atual
                                        if char['text'].isspace() or (len(words_info) > 0 and char['x0'] - current_x_end > 5):
                                            if current_word.strip():
                                                words_info.append({
                                                    'text': current_word.strip(),
                                                    'x0': current_x_start,
                                                    'x1': current_x_end
                                                })
                                            current_word = char['text']
                                            current_x_start = char['x0']
                                        else:
                                            current_word += char['text']
                                        
                                        current_x_end = char['x1']
                                    
                                    # Adicionar a última palavra
                                    if current_word.strip():
                                        words_info.append({
                                            'text': current_word.strip(),
                                            'x0': current_x_start,
                                            'x1': current_x_end
                                        })
                                    
                                    # Buscar a linha em inglês (próxima linha)
                                    for next_english_y, next_english_chars in sorted_char_lines:
                                        if next_english_y > header_y and next_english_y <= header_y + 25:  # Dentro de 25 pixels abaixo
                                            next_english_text = ''.join([c['text'] for c in sorted(next_english_chars, key=lambda c: c['x0'])])
                                            
                                            # Verificar se contém palavras-chave dos headers em inglês
                                            if any(keyword in next_english_text for keyword in [
                                                'Start Time', 'End Time', 'Equipment', 'Category', 'Line',
                                                'Manifest', 'Consignee', 'Shipper', 'Notes'
                                            ]):
                                                header_english_y = next_english_y
                                                
                                                # Extrair as palavras e suas coordenadas X da linha em inglês
                                                sorted_english_chars = sorted(next_english_chars, key=lambda c: c['x0'])
                                                
                                                # Capturar cada palavra individual com suas coordenadas
                                                english_words_info = []
                                                current_word = ""
                                                current_x_start = None
                                                current_x_end = None
                                                
                                                for char in sorted_english_chars:
                                                    if current_x_start is None:
                                                        current_x_start = char['x0']
                                                    
                                                    # Se é um espaço ou gap grande, finaliza a palavra atual
                                                    if char['text'].isspace() or (len(english_words_info) > 0 and char['x0'] - current_x_end > 5):
                                                        if current_word.strip():
                                                            english_words_info.append({
                                                                'text': current_word.strip(),
                                                                'x0': current_x_start,
                                                                'x1': current_x_end
                                                            })
                                                        current_word = char['text']
                                                        current_x_start = char['x0']
                                                    else:
                                                        current_word += char['text']
                                                    
                                                    current_x_end = char['x1']
                                                
                                                # Adicionar a última palavra
                                                if current_word.strip():
                                                    english_words_info.append({
                                                        'text': current_word.strip(),
                                                        'x0': current_x_start,
                                                        'x1': current_x_end
                                                    })
                                                
                                                header_columns = {
                                                    'portuguese': {word['text']: {'x0': word['x0'], 'x1': word['x1']} for word in words_info},
                                                    'english': {word['text']: {'x0': word['x0'], 'x1': word['x1']} for word in english_words_info}
                                                }
                                                break
                                    
                                    section_data = {
                                        "Title": title_text,
                                        "Y_coordinate": y,
                                        "Page": page_num + 1,
                                        "Header_columns": header_columns,
                                        "Header_Y": header_y,
                                        "Header_English_Y": header_english_y
                                    }
                                    
                                    sections_data.append(section_data)
    
    return sections_data

def extract_header_info(stream):
    """
    Extrai os dados do cabeçalho do relatório (cliente, cnpj, navio, atração, demonstrativo, valor bruto, moeda).
    """
    with pdfplumber.open(stream) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()

    header = {}
    # Cliente - capturar apenas até o próximo campo
    m = re.search(r'CLIENTE:\s*(.*?)(?=\s*NAVIO:)', text, re.DOTALL)
    if m:
        header["Cliente (Customer)"] = m.group(1).strip()
    
    # CNPJ
    m = re.search(r'CNPJ:\s*([\d\.\/\-]+)', text)
    if m:
        header["CNPJ (TAX_ID)"] = m.group(1).replace('.', '').replace('/', '').replace('-', '')
    
    # Navio - capturar apenas até o próximo campo
    m = re.search(r'NAVIO:\s*(.*?)(?=\s*DEMONSTRATIVO:)', text, re.DOTALL)
    if m:
        header["Navio (Viessel)"] = m.group(1).strip()
    
    # Atração
    m = re.search(r'ATRAÇÃO:\s*(.*?)(?=\s*DEMONSTRATIVO:|\s*VALOR BRUTO:|\n|$)', text, re.DOTALL)
    if m:
        valor = m.group(1).strip()
        header["Atração (BERTH_ATA)"] = valor if valor else None
    else:
        header["Atração (BERTH_ATA)"] = None
    
    # Demonstrativo
    m = re.search(r'DEMONSTRATIVO:\s*(\d+)', text)
    if m:
        header["Demonstrativo (Draft)"] = m.group(1)
    
    # Valor Bruto
    m = re.search(r'VALOR BRUTO R\$:\s*\(BRL\)\s*([\d\.,]+)', text)
    if m:
        valor = m.group(1).replace('.', '').replace(',', '.')
        try:
            header["Valor Bruto"] = float(valor)
        except:
            header["Valor Bruto"] = None
    
    # Moeda
    header["Moeda"] = "BRL"
    return {"header": header}

def is_footer_line(line_text):
    rodape_keywords = [
        'Obs1', 'Obs2', 'VALOR BRUTO', 'nota fiscal', 'EMBRAPORT', 'CEP', 'Telefone', 'www.dpworldsantos.com',
        'Estrada Particular', 'Santos', 'CNPJ', 'EGA ASSESSORIA', 'LOGSEAIR', 'DRAFT', 'CUSTOMER', 'VESSEL', 'ATA', 'DRAFT', 'TAX_ID'
    ]
    return any(kw.lower() in line_text.lower() for kw in rodape_keywords)

def is_header_line(line_text):
    # Se contém 'AmountTotal', não é header
    if 'AmountTotal' in line_text:
        return False
    
    header_keywords = [
        'Data Inicial', 'Data Final', 'Container', 'Categoria', 'Armador', 'Manifesto', 'Importador', 'Exportador', 'Observacoes',
        'Start Time', 'End Time', 'Equipment', 'Category', 'Line', 'Manifest', 'Consignee', 'Shipper', 'Notes', 'Quantity', 'Total'
    ]
    return any(kw.lower() in line_text.lower() for kw in header_keywords)

def is_valid_data_row(row):
    # Considera válido se tem CNPJ e pelo menos Data Inicial e Container
    cnpj = row.get('CNPJ / CPF (ID)', '')
    data_inicial = row.get('Data Inicial (Start Time)', '')
    container = row.get('Container (Equipment ID)', '')
    cnpj = cnpj.strip() if isinstance(cnpj, str) else ''
    data_inicial = data_inicial.strip() if isinstance(data_inicial, str) else ''
    container = container.strip() if isinstance(container, str) else ''
    return cnpj and data_inicial and container

def extract_data_with_header_mapping(stream):
    """
    Extrai dados usando o mapeamento específico das coordenadas X das colunas do header, agrupando linhas de conteúdo até a próxima linha azul, e retorna no formato organizado. Cria apenas um registro por seção. Ignora rodapé e header baseado em coordenada Y.
    """
    # Definir coordenadas Y para otimização
    PAGE1_START_Y = 159.0  # Página 1: após o header principal
    OTHER_PAGES_START_Y = 67.5  # Páginas 2+: após título/logo
    FOOTER_Y_MIN = 515.0  # Rodapé (baseado no debug)
    
    header_mapping = {
        'Data Inicial (Start Time)': {'x0': 7.2, 'x1': 40.6},
        'Data Final (End Time)': {'x0': 47.0, 'x1': 78.0},
        'Container (Equipment ID)': {'x0': 86.1, 'x1': 128.8},
        'Categoria (Category)': {'x0': 134.9, 'x1': 164.9},
        'Armador (Line)': {'x0': 169.4, 'x1': 194.4},
        'Manifesto Carga BL / Booking': {'x0': 199.5, 'x1': 250.0},
        'Importador/Exportador (Consignee / Shipper)': {'x0': 250.8, 'x1': 334.0},
        'CNPJ / CPF (ID)': {'x0': 335.0, 'x1': 390.0},
        'DT / DTA': {'x0': 392.0, 'x1': 439.0},
        'GMCI / GRCI': {'x0': 440.2, 'x1': 483.9},
        'Doc': {'x0': 491.0, 'x1': 532.0},
        'Referência (Reference)': {'x0': 540.5, 'x1': 575.5},
        'DIAS (Days)': {'x0': 579.9, 'x1': 598.3},
        'Observacoes (Notes)': {'x0': 600.0, 'x1': 750.0},
        'Moeda (Currency)': {'x0': 751.3, 'x1': 781.7},
        'Valor (Unit Value)': {'x0': 788.0, 'x1': 831.0}
    }
    
    def is_blue_line(y_coord, lines, rects):
        """Verifica se uma coordenada Y tem uma linha/retângulo azul"""
        # Verificar linhas
        for line in lines:
            if abs(line['top'] - y_coord) < 5:
                if 'stroking_color' in line and str(line['stroking_color']) == "(0.098, 0.098, 0.439)":
                    return True
                elif 'non_stroking_color' in line and str(line['non_stroking_color']) == "(0.098, 0.098, 0.439)":
                    return True
        # Verificar retângulos
        for rect in rects:
            if abs(rect['top'] - y_coord) < 5:
                if 'non_stroking_color' in rect and str(rect['non_stroking_color']) == "(0.098, 0.098, 0.439)":
                    return True
                elif 'stroking_color' in rect and str(rect['stroking_color']) == "(0.098, 0.098, 0.439)":
                    return True
        return False
    
    def extract_text_by_coordinates(chars_list, x0, x1):
        filtered_chars = [char for char in chars_list if x0 <= char['x0'] <= x1]
        if filtered_chars:
            sorted_chars = sorted(filtered_chars, key=lambda c: c['x0'])
            return ''.join([c['text'] for c in sorted_chars]).strip()
        return ''
    
    sections_data = []
    
    with pdfplumber.open(stream) as pdf:
        for page_num, page in enumerate(pdf.pages):
            lines = page.lines
            rects = page.rects
            chars = page.chars
            char_lines = {}
            for char in chars:
                y_key = round(char['top'], 1)
                if y_key not in char_lines:
                    char_lines[y_key] = []
                char_lines[y_key].append(char)
            sorted_char_lines = sorted(char_lines.items(), key=lambda x: x[0])
            
            # PASSO 1: Mapear todas as seções (linhas azuis)
            blue_sections = []
            for i, (y, line_chars) in enumerate(sorted_char_lines):
                if page_num == 0 and y <= PAGE1_START_Y:
                    continue
                elif page_num > 0 and y <= OTHER_PAGES_START_Y:
                    continue
                if y >= FOOTER_Y_MIN:
                    continue
                if is_blue_line(y, lines, rects):
                    sorted_chars = sorted(line_chars, key=lambda c: c['x0'])
                    title_text = extract_text_by_coordinates(sorted_chars, 7.2, 400)
                    quantidade_text = extract_text_by_coordinates(sorted_chars, 540, 700)
                    total_text = extract_text_by_coordinates(sorted_chars, 700, 820.8)
                    total_value = None
                    if total_text:
                        numbers = re.findall(r'[\d\.,]+', total_text)
                        if numbers:
                            total_value = numbers[0].replace('.', '').replace(',', '.')
                            try:
                                total_value = float(total_value)
                            except:
                                total_value = None
                    quantidade_value = None
                    if quantidade_text:
                        numbers = re.findall(r'\d+', quantidade_text)
                        if numbers:
                            quantidade_value = int(numbers[0])
                    if title_text and any(section in title_text for section in [
                        'Armazenagem', 'Cadastro', 'Handling', 'Presenca', 'Repasse', 'Scanner']):
                        blue_sections.append({
                            'y': y,
                            'index': i,
                            'title': title_text,
                            'quantidade': quantidade_value,
                            'total': total_value
                        })
            # PASSO 2: Processar cada seção individualmente
            for section_idx, section_info in enumerate(blue_sections):
                section_y = section_info['y']
                section_index = section_info['index']
                next_section_y = None
                if section_idx + 1 < len(blue_sections):
                    next_section_y = blue_sections[section_idx + 1]['y']
                header_pt_found = False
                header_en_found = False
                data_start_index = None
                for j in range(section_index + 1, len(sorted_char_lines)):
                    y, chars_line = sorted_char_lines[j]
                    if next_section_y and y >= next_section_y:
                        break
                    if page_num == 0 and y <= PAGE1_START_Y:
                        continue
                    elif page_num > 0 and y <= OTHER_PAGES_START_Y:
                        continue
                    if y >= FOOTER_Y_MIN:
                        break
                    line_text = ''.join([c['text'] for c in sorted(chars_line, key=lambda c: c['x0'])])
                    if not header_pt_found and any(keyword in line_text for keyword in [
                        'Data Inicial', 'Data Final', 'Container', 'Categoria', 'Armador',
                        'Manifesto', 'Importador', 'Exportador', 'Observacoes']):
                        header_pt_found = True
                        continue
                    if header_pt_found and not header_en_found and any(keyword in line_text for keyword in [
                        'Start Time', 'End Time', 'Equipment', 'Category', 'Line',
                        'Manifest', 'Consignee', 'Shipper', 'Notes']):
                        header_en_found = True
                        data_start_index = j + 1
                        break
                section_fields = []
                if data_start_index:
                    k = data_start_index
                    while k < len(sorted_char_lines):
                        content_y, content_chars = sorted_char_lines[k]
                        if next_section_y and content_y >= next_section_y:
                            break
                        if page_num == 0 and content_y <= PAGE1_START_Y:
                            k += 1
                            continue
                        elif page_num > 0 and content_y <= OTHER_PAGES_START_Y:
                            k += 1
                            continue
                        if content_y >= FOOTER_Y_MIN:
                            break
                        content_text = ''.join([c['text'] for c in sorted(content_chars, key=lambda c: c['x0'])])
                        if is_header_line(content_text):
                            k += 1
                            continue
                        row = {}
                        for field_name, coords in header_mapping.items():
                            field_value = extract_text_by_coordinates(content_chars, coords['x0'], coords['x1'])
                            row[field_name] = field_value if field_value else None
                        if is_valid_data_row(row):
                            k_next = k + 1
                            while k_next < len(sorted_char_lines):
                                next_y, next_chars = sorted_char_lines[k_next]
                                if next_section_y and next_y >= next_section_y:
                                    break
                                if next_y >= FOOTER_Y_MIN:
                                    break
                                next_text = ''.join([c['text'] for c in sorted(next_chars, key=lambda c: c['x0'])])
                                if is_header_line(next_text):
                                    break
                                next_row = {}
                                for field_name, coords in header_mapping.items():
                                    field_value = extract_text_by_coordinates(next_chars, coords['x0'], coords['x1'])
                                    next_row[field_name] = field_value if field_value else None
                                
                                # Se a próxima linha tem CNPJ, Data Inicial E Container, é um novo registro
                                has_cnpj = next_row.get('CNPJ / CPF (ID)') and len(next_row.get('CNPJ / CPF (ID)', '')) > 10
                                has_data_inicial = next_row.get('Data Inicial (Start Time)') and '/' in next_row.get('Data Inicial (Start Time)', '')
                                has_container = next_row.get('Container (Equipment ID)') and len(next_row.get('Container (Equipment ID)', '')) > 5
                                
                                if has_cnpj and has_data_inicial and has_container:
                                    break
                                # Concatenar Observações (Notes) e outros campos que podem ser multi-linha
                                multi_line_fields = ['Observacoes (Notes)', 'Importador/Exportador (Consignee / Shipper)', 'Manifesto Carga BL / Booking']
                                for field_name in multi_line_fields:
                                    field_value_next = extract_text_by_coordinates(next_chars, header_mapping[field_name]['x0'], header_mapping[field_name]['x1'])
                                    if field_value_next:
                                        if row[field_name]:
                                            row[field_name] += ' ' + field_value_next
                                        else:
                                            row[field_name] = field_value_next
                                k_next += 1
                            processed_row = {field_name: (value.strip() if isinstance(value, str) and value.strip() else None)
                                           for field_name, value in row.items()}
                            section_fields.append(processed_row)
                            k = k_next
                        else:
                            k += 1
                if section_fields:
                    section_data = {
                        "Quantidade (Quantity)": section_info['quantidade'],
                        "Title": section_info['title'],
                        "Total": section_info['total'],
                        "fields": section_fields
                    }
                    sections_data.append(section_data)
    return sections_data

def read_pdf_and_analyze(stream):
    """
    Função principal que analisa o PDF e retorna a estrutura no formato pedido
    """
    try:
        # Extrair header
        header_info = extract_header_info(stream)
        # Extrair dados usando o mapeamento do header
        sections_with_data = extract_data_with_header_mapping(stream)
        return {
            "header": header_info["header"],
            "sections": sections_with_data
        }
    except Exception as e:
        return {
            "error": str(e),
            "header": {},
            "sections": []
        } 