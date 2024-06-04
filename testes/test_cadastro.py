import pytest
from run import Usuario, Endereco, db
from wtforms import StringField, PasswordField, validators

def test_cadastro_sucesso(test_client): 
    # Dados de teste válidos
    dados_cadastro = { 
                      'nome': 'João', 
                      'estado': 'SP', 
                      'endereco': 'Rua Exemplo',
                      'cep': '12345678', 
                      'cidade': 'São Paulo', 
                      'telefone': '1234567890',
                      'email': 'joao@example.com', 
                      'senha': '123456' } 
    # Enviar a requisição POST para a rota /cadastro 
    response = test_client.post('/cadastro', data=dados_cadastro, follow_redirects=True)
    # Verificar se ocorreram erros de campos vazios > 
    assert response.status_code == 200
    

def test_cadastro_email_existente(test_client):
    # Criar um usuário existente
    usuario_existente = Usuario(nome='João', email='joao@example.com', uid='123456')
    db.session.add(usuario_existente)
    db.session.commit()

    # Dados de teste com email existente
    dados_cadastro = {
        'nome': 'Maria',
        'email': 'joao@example.com',
        'senha': 'senha123',
        'estado': 'SP',
        'endereco': 'Rua Exemplo, 123',
        'cep': '12345-678',
        'cidade': 'São Paulo',
        'telefone': '1234567890'
    }

    # Enviar a requisição POST para a rota /cadastro
    response = test_client.post('/cadastro', data=dados_cadastro, follow_redirects=True)

    # Verificar se ocorreu um erro de email existente
    assert b'O email fornecido j\xc3\xa1 est\xc3\xa1 em uso' in response.data

def test_cadastro_campos_vazios(test_client):
    # Dados de teste com campos vazios
    dados_cadastro = {
        'nome': '',
        'estado': '',
        'endereco': '',
        'cep': '',
        'cidade': '',
        'telefone': '',
        'email': '',
        'senha': ''
    }

    # Enviar a requisição POST para a rota /cadastro
    response = test_client.post('/cadastro', data=dados_cadastro, follow_redirects=True)

    # Verificar se ocorreram erros de campos vazios
    assert b'Todos os campos s\xc3\xa3o obrigat\xc3\xb3rios.' in response.data

def test_cadastro_email_invalido(test_client):
    # Dados de teste com email inválido
    dados_cadastro = {
        'nome': 'João',
        'email': 'joaoinvalido',
        'senha': 'senha123',
        'estado': 'SP',
        'endereco': 'Rua Exemplo, 123',
        'cep': '12345-678',
        'cidade': 'São Paulo',
        'telefone': '1234567890'
    }

    # Enviar a requisição POST para a rota /cadastro
    response = test_client.post('/cadastro', data=dados_cadastro, follow_redirects=True)

    # Verificar se ocorreu um erro de email inválido
    assert b'Formato de email inv\xc3\xa1lido.' in response.data