import pytest
from run import Usuario,  db
from conftest import test_client

def test_login_sucesso(test_client):
    # Criar um usuário existente
    usuario_existente = Usuario(nome='João', email='joao@example.com', uid='123456')
    db.session.add(usuario_existente)
    db.session.commit() 

    # Dados de teste válidos
    dados_login = {
        'email': 'joao@example.com',
        'senha': 'senha123'
    }

    # Enviar a requisição POST para a rota /login
    response = test_client.post('/login', data=dados_login, follow_redirects=True)

    # Verificar se o login foi bem-sucedido
    assert response.status_code == 200
    

def test_login_senha_invalida(test_client):
    # Criar um usuário existente
    usuario_existente = Usuario(nome='João', email='joao@example.com', uid='123456')
    db.session.add(usuario_existente)
    db.session.commit()

    # Dados de teste com senha inválida
    dados_login = {
        'email': 'joao@example.com',
        'senha': 'senhaincorreta'
    }

    # Enviar a requisição POST para a rota /login
    response = test_client.post('/login', data=dados_login, follow_redirects=True)

    # Verificar se ocorreu um erro de credenciais inválidas
    assert b'Credenciais inv\xc3\xa1lidas.' in response.data