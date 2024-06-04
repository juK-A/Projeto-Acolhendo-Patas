import pytest
from run import app, db, Usuario, Animal
import uuid

@pytest.fixture
def usuario_de_teste():
    with app.app_context():
        db.session.query(Usuario).delete()  # Limpar a tabela de usuários
        db.session.commit()
        uid = str(uuid.uuid4())  # Gerar um UID único
        usuario = Usuario(uid=uid, nome='Teste', email='teste@example.com')
        db.session.add(usuario)
        db.session.commit()
        yield usuario
        db.session.delete(usuario)
        db.session.commit()


@pytest.fixture
def animal_de_teste(usuario_de_teste):
    with app.app_context():
        animal = Animal(id=1, nome='Rex', especie='Cachorro', porte='Grande', sexo='Macho', raca='Labrador', descricao='Um cachorro amigável', idade='5', usuario_id=usuario_de_teste.id)
        db.session.add(animal)
        db.session.commit()
        yield animal
        db.session.delete(animal)
        db.session.commit()
    
@pytest.fixture
def test_client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
        db.session.remove()
        db.drop_all()
        

@pytest.fixture
def authenticated_client(test_client):
    # Criar um usuário e fazer login
    usuario = Usuario(nome='Teste', email='teste@teste.com', uid='123')
    db.session.add(usuario)
    db.session.commit()
    
    with test_client.session_transaction() as session:
        session['uid'] = '123'
    
    return test_client
