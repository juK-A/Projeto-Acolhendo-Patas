import pytest
from run import Usuario, Endereco, db, app

import pytest


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

@pytest.fixture
def usuario_e_endereco():
    with app.app_context():
        usuario = Usuario(uid='test_uid', nome='Test User', email='test@example.com')
        db.session.add(usuario)
        db.session.commit()
        endereco = Endereco(usuario_id=usuario.id, estado='Test State', endereco='Test Address', cep='12345-678', telefone='(11) 91234-5678', cidade='Test City')
        db.session.add(endereco)
        db.session.commit()
        return usuario, endereco

def login(client, usuario):
    with client.session_transaction() as session:
        session['uid'] = usuario.uid
        session['nome_usuario'] = usuario.nome

def test_editar_usuario_get(client, usuario_e_endereco):
    usuario, endereco = usuario_e_endereco
    with app.app_context():
        login(client, usuario)
        response = client.get('/editar_usuario')
        assert response.status_code == 200
        assert b'Editar Usu\xc3\xa1rio' in response.data

def test_editar_usuario_post(authenticated_client):
    usuario, endereco = usuario_e_endereco
    with app.test_client() as client:
        # Autenticar o usuário antes de enviar a requisição POST
        with client.session_transaction() as session:
            session['uid'] = usuario.uid
            session['nome_usuario'] = usuario.nome

        # Simular o envio do formulário com os dados atualizados
        data = {
            'nome': 'Novo Nome',
            'email': 'novo_email@example.com',
            'senha': 'nova_senha',
            'telefone': '(11) 98765-4321',
            'estado': 'Novo Estado',
            'endereco': 'Nova Rua, 123',
            'cep': '12345-678',
            'cidade': 'Nova Cidade'
        }

        response = client.post('/editar_usuario', data=data, follow_redirects=True)
        
        # Verificar se a atualização foi bem-sucedida
        assert response.status_code == 200
    