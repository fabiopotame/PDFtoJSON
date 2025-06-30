import re
import pdfplumber
from PyPDF2 import PdfReader

# Constants for coordinates and configurations
PAGE1_START_Y = 159.0
OTHER_PAGES_START_Y = 67.5
FOOTER_Y_MIN = 515.0
BLUE_COLOR = "(0.098, 0.098, 0.439)"

# Header column mapping
HEADER_MAPPING = {
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

# Fields that can be multi-line - ALL fields can be multi-line
MULTI_LINE_FIELDS = list(HEADER_MAPPING.keys())

# Keywords to identify valid sections
VALID_SECTIONS = ['Armazenagem', 'Cadastro', 'Handling', 'Presenca', 'Repasse', 'Scanner']

# Keywords to identify Portuguese headers
PORTUGUESE_HEADER_KEYWORDS = [
    'Data Inicial', 'Data Final', 'Container', 'Categoria', 'Armador',
    'Manifesto', 'Importador', 'Exportador', 'Observacoes'
]

# Keywords to identify English headers
ENGLISH_HEADER_KEYWORDS = [
    'Start Time', 'End Time', 'Equipment', 'Category', 'Line',
    'Manifest', 'Consignee', 'Shipper', 'Notes'
]

def extract_header_info(stream):
    """
    Extracts header data from the report (client, cnpj, vessel, berth, draft, gross value, currency).
    """
    with pdfplumber.open(stream) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()

    header = {}
    
    # Client - capture only until the next field
    m = re.search(r'CLIENTE:\s*(.*?)(?=\s*NAVIO:)', text, re.DOTALL)
    if m:
        header["Cliente (Customer)"] = m.group(1).strip()
    
    # CNPJ
    m = re.search(r'CNPJ:\s*([\d\.\/\-]+)', text)
    if m:
        header["CNPJ (TAX_ID)"] = m.group(1).replace('.', '').replace('/', '').replace('-', '')
    
    # Vessel - capture only until the next field
    m = re.search(r'NAVIO:\s*(.*?)(?=\s*DEMONSTRATIVO:)', text, re.DOTALL)
    if m:
        header["Navio (Viessel)"] = m.group(1).strip()
    
    # Berth
    m = re.search(r'ATRAÇÃO:\s*(.*?)(?=\s*DEMONSTRATIVO:|\s*VALOR BRUTO:|\n|$)', text, re.DOTALL)
    if m:
        valor = m.group(1).strip()
        header["Atração (BERTH_ATA)"] = valor if valor else None
    else:
        header["Atração (BERTH_ATA)"] = None
    
    # Draft
    m = re.search(r'DEMONSTRATIVO:\s*(\d+)', text)
    if m:
        header["Demonstrativo (Draft)"] = m.group(1)
    
    # Gross Value
    m = re.search(r'VALOR BRUTO R\$:\s*\(BRL\)\s*([\d\.,]+)', text)
    if m:
        valor = m.group(1).replace('.', '').replace(',', '.')
        try:
            header["Valor Bruto"] = float(valor)
        except:
            header["Valor Bruto"] = None
    
    # Currency
    header["Moeda"] = "BRL"
    return {"header": header}

def is_blue_line(y_coord, lines, rects):
    """Checks if a Y coordinate has a blue line/rectangle"""
    # Check lines
    for line in lines:
        if abs(line['top'] - y_coord) < 5:
            if 'stroking_color' in line and str(line['stroking_color']) == BLUE_COLOR:
                return True
            elif 'non_stroking_color' in line and str(line['non_stroking_color']) == BLUE_COLOR:
                return True
    
    # Check rectangles
    for rect in rects:
        if abs(rect['top'] - y_coord) < 5:
            if 'non_stroking_color' in rect and str(rect['non_stroking_color']) == BLUE_COLOR:
                return True
            elif 'stroking_color' in rect and str(rect['stroking_color']) == BLUE_COLOR:
                return True
    
    return False

def extract_text_by_coordinates(chars_list, x0, x1):
    """Extracts text from a character list based on X coordinates"""
    filtered_chars = [char for char in chars_list if x0 <= char['x0'] <= x1]
    if filtered_chars:
        sorted_chars = sorted(filtered_chars, key=lambda c: c['x0'])
        return ''.join([c['text'] for c in sorted_chars]).strip()
    return ''

def is_header_line(line_text):
    """Checks if a line is a header (contains header keywords)"""
    if 'AmountTotal' in line_text:
        return False
    
    header_keywords = PORTUGUESE_HEADER_KEYWORDS + ENGLISH_HEADER_KEYWORDS + ['Quantity', 'Total']
    return any(kw.lower() in line_text.lower() for kw in header_keywords)

def is_valid_data_row(row):
    """Checks if a data row is valid (has CNPJ, Start Date and Container)"""
    cnpj = row.get('CNPJ / CPF (ID)', '')
    data_inicial = row.get('Data Inicial (Start Time)', '')
    container = row.get('Container (Equipment ID)', '')
    
    cnpj = cnpj.strip() if isinstance(cnpj, str) else ''
    data_inicial = data_inicial.strip() if isinstance(data_inicial, str) else ''
    container = container.strip() if isinstance(container, str) else ''
    
    return cnpj and data_inicial and container

def is_new_record(next_row):
    """Checks if the next line represents a new record"""
    has_cnpj = next_row.get('CNPJ / CPF (ID)') and len(next_row.get('CNPJ / CPF (ID)', '')) > 10
    has_data_inicial = next_row.get('Data Inicial (Start Time)') and '/' in next_row.get('Data Inicial (Start Time)', '')
    has_container = next_row.get('Container (Equipment ID)') and len(next_row.get('Container (Equipment ID)', '')) > 5
    
    return has_cnpj and has_data_inicial and has_container

def extract_section_data(page_num, sorted_char_lines, lines, rects):
    """Extracts data from a specific section"""
    sections_data = []
    
    # STEP 1: Map all sections (blue lines)
    blue_sections = []
    for i, (y, line_chars) in enumerate(sorted_char_lines):
        # Skip lines outside boundaries
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
            
            # Extract numeric values
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
            
            # Check if it's a valid section
            if title_text and any(section in title_text for section in VALID_SECTIONS):
                blue_sections.append({
                    'y': y,
                    'index': i,
                    'title': title_text,
                    'quantidade': quantidade_value,
                    'total': total_value
                })
    
    # STEP 2: Process each section individually
    for section_idx, section_info in enumerate(blue_sections):
        section_y = section_info['y']
        section_index = section_info['index']
        next_section_y = blue_sections[section_idx + 1]['y'] if section_idx + 1 < len(blue_sections) else None
        
        # Find headers and data start
        header_pt_found = False
        header_en_found = False
        data_start_index = None
        
        for j in range(section_index + 1, len(sorted_char_lines)):
            y, chars_line = sorted_char_lines[j]
            
            # Check boundaries
            if next_section_y and y >= next_section_y:
                break
            if page_num == 0 and y <= PAGE1_START_Y:
                continue
            elif page_num > 0 and y <= OTHER_PAGES_START_Y:
                continue
            if y >= FOOTER_Y_MIN:
                break
            
            line_text = ''.join([c['text'] for c in sorted(chars_line, key=lambda c: c['x0'])])
            
            # Find Portuguese header
            if not header_pt_found and any(keyword in line_text for keyword in PORTUGUESE_HEADER_KEYWORDS):
                header_pt_found = True
                continue
            
            # Find English header
            if header_pt_found and not header_en_found and any(keyword in line_text for keyword in ENGLISH_HEADER_KEYWORDS):
                header_en_found = True
                data_start_index = j + 1
                break
        
        # Process section data
        section_fields = []
        if data_start_index:
            k = data_start_index
            while k < len(sorted_char_lines):
                content_y, content_chars = sorted_char_lines[k]
                
                # Check boundaries
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
                
                # Extract row data
                row = {}
                for field_name, coords in HEADER_MAPPING.items():
                    field_value = extract_text_by_coordinates(content_chars, coords['x0'], coords['x1'])
                    row[field_name] = field_value if field_value else None
                
                if is_valid_data_row(row):
                    # Concatenate continuation lines
                    k_next = k + 1
                    while k_next < len(sorted_char_lines):
                        next_y, next_chars = sorted_char_lines[k_next]
                        
                        # Check boundaries
                        if next_section_y and next_y >= next_section_y:
                            break
                        if next_y >= FOOTER_Y_MIN:
                            break
                        
                        next_text = ''.join([c['text'] for c in sorted(next_chars, key=lambda c: c['x0'])])
                        if is_header_line(next_text):
                            break
                        
                        # Check if it's a new record
                        next_row = {}
                        for field_name, coords in HEADER_MAPPING.items():
                            field_value = extract_text_by_coordinates(next_chars, coords['x0'], coords['x1'])
                            next_row[field_name] = field_value if field_value else None
                        
                        if is_new_record(next_row):
                            break
                        
                        # Concatenate multi-line fields
                        for field_name in MULTI_LINE_FIELDS:
                            field_value_next = extract_text_by_coordinates(next_chars, HEADER_MAPPING[field_name]['x0'], HEADER_MAPPING[field_name]['x1'])
                            if field_value_next:
                                if row[field_name]:
                                    row[field_name] += ' ' + field_value_next
                                else:
                                    row[field_name] = field_value_next
                        
                        k_next += 1
                    
                    # Process final row
                    processed_row = {field_name: (value.strip() if isinstance(value, str) and value.strip() else None)
                                   for field_name, value in row.items()}
                    section_fields.append(processed_row)
                    k = k_next
                else:
                    k += 1
        
        # Add section if it has data
        if section_fields:
            section_data = {
                "Quantidade (Quantity)": section_info['quantidade'],
                "Title": section_info['title'],
                "Total": section_info['total'],
                "fields": section_fields
            }
            sections_data.append(section_data)
    
    return sections_data

def extract_data_with_header_mapping(stream):
    """
    Extracts data using the specific X coordinate mapping of header columns.
    Groups content lines until the next blue line and returns in organized format.
    """
    sections_data = []
    
    with pdfplumber.open(stream) as pdf:
        for page_num, page in enumerate(pdf.pages):
            lines = page.lines
            rects = page.rects
            chars = page.chars
            
            # Group characters by line
            char_lines = {}
            for char in chars:
                y_key = round(char['top'], 1)
                if y_key not in char_lines:
                    char_lines[y_key] = []
                char_lines[y_key].append(char)
            
            sorted_char_lines = sorted(char_lines.items(), key=lambda x: x[0])
            
            # Extract page data
            page_sections = extract_section_data(page_num, sorted_char_lines, lines, rects)
            sections_data.extend(page_sections)
    
    return sections_data

def read_pdf_and_analyze(stream):
    """
    Main function that analyzes the PDF and returns the structure in the requested format
    """
    try:
        # Extract header
        header_info = extract_header_info(stream)
        # Extract data using header mapping
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