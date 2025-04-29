import re
import pdfplumber
from PyPDF2 import PdfReader

SECTIONS = [
    'Armazenagem Importacao FCL Cheio "40"',
    'Cadastro de BL',
    'Handling - Out',
    'Handling - In',
    'Handling Entre Margem "40"',
    'Presenca de Carga',
    'Repasse Codesp - Tabela III',
    'Scanner',
]

def extract_text(stream):
    with pdfplumber.open(stream) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)

def read_metadata(stream):
    reader = PdfReader(stream)
    raw = reader.metadata or {}
    return {k.lstrip('/'): raw[k] for k in raw}

def parse_header_block(text):
    header = {}
    m = re.search(r'CLIENTE:\s*(.*?)\s*NAVIO:', text, re.S)
    if m:
        header["Cliente (Customer)"] = m.group(1).strip()
    m = re.search(r'CNPJ:\s*(\d+)', text)
    if m:
        header["CNPJ (Tax_id)"] = m.group(1)
    m = re.search(r'NAVIO:\s*(.*?)\s+DEMONSTRATIVO:', text, re.S)
    if m:
        header["NAVIO (Vessel)"] = m.group(1).strip()
    m = re.search(r'ATRAÇÂO:\s*(.*?)\s', text)
    if m:
        valor = m.group(1).strip()
        if not valor or valor.upper() in ["VALOR", "BRUTO", "R$", "TOTAL"]:
            header["ATRAÇÂO (Berth_ata)"] = None
        else:
            header["ATRAÇÂO (Berth_ata)"] = valor
    else:
        header["ATRAÇÂO (Berth_ata)"] = None
    m = re.search(r'DEMONSTRATIVO:\s*(\d+)', text)
    if m:
        header["DEMONSTRATIVO (Draft)"] = m.group(1)
    m = re.search(r'VALOR BRUTO R\$:\s*\(BRL\)\s*([\d\.,]+)', text)
    if m:
        valor = m.group(1).replace('.', '').replace(',', '.')
        header["VALOR BRUTO R$: (BRL)"] = float(valor)
    return header

def parse_section(section_name, full_text):
    parts = full_text.split(section_name, 1)
    if len(parts) < 2:
        return None
    block = parts[1]
    for nxt in SECTIONS:
        if nxt == section_name:
            continue
        block = block.split(nxt, 1)[0]

    lines = [l.strip() for l in block.splitlines() if l.strip()]
    if not lines:
        return None

    result = {"Title": section_name}

    m = re.search(r'Quantidade.*?(\d+).*?Total.*?([\d\.,]+)', lines[0])
    if m:
        result["Quantidade (Quantity)"] = int(m.group(1))
        result["Total"] = float(m.group(2).replace('.', '').replace(',', '.'))

    hdr_idx = next((i for i, l in enumerate(lines) if l.startswith('Data Inicial')), None)
    if hdr_idx is None or hdr_idx+2 >= len(lines):
        return result

    headers_line = lines[hdr_idx]
    values_line = lines[hdr_idx+2]

    header_tokens = headers_line.split()
    value_tokens = values_line.split()

    mapping = [
        ("Data Inicial (Start Time)", 0),
        ("Data Final (End Time)", 1),
        ("Container (Equipment ID)", 2),
        ("Categoria (Category)", 3),
        ("Armador (Line)", 4),
        ("Manifesto Carga BL / Booking", 5),
        ("Importador/Exportador (Consignee / Shipper)", 6),
        ("CNPJ / CPF (ID)", 7),
        ("DT / DTA", 8),
        ("GMCI / GRCI", 9),
        ("Doc", 10),
        ("Referência (Reference)", 11),
        ("DIAS (Days)", 12),
        ("Moeda (Currency)", -2),
        ("Valorc(Unit Value)", -1),
    ]

    fields = {}
    for key, idx in mapping:
        if idx >= 0 and idx < len(value_tokens):
            fields[key] = value_tokens[idx]
        elif idx < 0 and abs(idx) <= len(value_tokens):
            fields[key] = value_tokens[idx]
        else:
            fields[key] = None

    observacoes = []
    for l in lines[hdr_idx+3:]:
        pm = re.match(r'(P\d+)\s+(\d{2}/\d{2}/\d{4})\s+à\s+(\d{2}/\d{2}/\d{4}).*?=\s*([\d\.,]+)', l)
        if pm:
            observacoes.append(f"{pm.group(1)} {pm.group(2)} à {pm.group(3)} valor {pm.group(4)}")

    if observacoes:
        fields["Observacoes (Notes)"] = "\n".join(observacoes)

    result["fields"] = fields
    return result

def extract_tables(stream):
    full_text = extract_text(stream)
    body = []
    for sec in SECTIONS:
        data = parse_section(sec, full_text)
        if data:
            body.append(data)
    header = parse_header_block(full_text)
    return header, body

def read_pdf_and_group(stream):
    metadata = read_metadata(stream)
    stream.seek(0)
    header, body = extract_tables(stream)
    return {
        "metadata": metadata,
        "header": header,
        "body": body
    }
