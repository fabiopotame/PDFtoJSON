import io
import json
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_convert_endpoint(client):
    # Carrega um PDF de exemplo
    with open('tests/samples/DRAFT_1042716.pdf', 'rb') as pdf_file:
        data = {
            'file': (pdf_file, 'DRAFT_1042716.pdf')
        }
        response = client.post('/convert', content_type='multipart/form-data', data=data)

    assert response.status_code == 200
    assert response.is_json

    resp_json = response.get_json()

    # Verifica a estrutura principal
    assert 'header' in resp_json
    assert 'body' in resp_json
    assert 'metadata' in resp_json

    header = resp_json['header']
    body = resp_json['body']
    metadata = resp_json['metadata']

    # Testa campos no header
    assert 'Cliente (Customer)' in header
    assert 'CNPJ (Tax_id)' in header
    assert 'NAVIO (Vessel)' in header

    # Testa body
    assert isinstance(body, list)
    assert len(body) > 0

    for item in body:
        assert 'Title' in item
        assert 'Quantidade (Quantity)' in item
        assert 'Total' in item
        assert 'fields' in item
        fields = item['fields']
        assert isinstance(fields, dict)
        assert 'Data Inicial (Start Time)' in fields
        assert 'Container (Equipment ID)' in fields

    # Testa metadata básica
    assert 'Title' in metadata
    assert 'Creator' in metadata

