import json
import os
import pytest
from pdf2json import pdf_fixed_parser

def test_pdf_fixed_parser_response_matches_model():
    modelo_path = os.path.join('temp', 'modelo_response.json')
    pdf_path = os.path.join('temp', '55600-demo.pdf')
    with open(modelo_path, 'r', encoding='utf-8') as f:
        modelo = json.load(f)
    with open(pdf_path, 'rb') as f:
        response = pdf_fixed_parser.read_pdf_and_analyze_fixed(f)
    # Comparação direta dos dicionários
    assert response == modelo, f"Resposta do parser diferente do modelo!\nDiferença: {json.dumps(response, indent=2, ensure_ascii=False)}" 