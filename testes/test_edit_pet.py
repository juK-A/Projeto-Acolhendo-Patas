from flask_testing import TestCase
from run import db, Usuario, Animal

class TestClient(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'  # ou o seu banco de dados de teste
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()


from run import app, db, Usuario, Animal

def login(client, email, senha):
    return client.post('/login', data=dict(
        email=email,
        senha=senha
    ), follow_redirects=True)

def test_editar_animal_sucesso(test_client, usuario_de_teste):

    animal = Animal(nome='Antigo Nome', idade=3, descricao='Antiga descrição', especie='Cachorro', porte='Médio', sexo='Macho', raca='SRD', usuario_id=usuario_de_teste.id)
    db.session.add(animal)
    db.session.commit()

    # Dados de exemplo para editar um animal
    dados_editados = {
        'nome': 'Novo Nome',
        'idade': 5,
        'descricao': 'Descrição atualizada',
        'especie': 'Gato',
        'porte': 'Pequeno',
        'sexo': 'Fêmea',
        'raca': 'Persa'
    }

    # Fazer uma solicitação para editar o animal
    response = test_client.post(f'/editar_animal/{animal.id}', data=dados_editados, follow_redirects=True)

    # Verificar se a resposta foi bem-sucedida
    assert response.status_code == 200

    # Verificar se os dados do animal foram atualizados corretamente no banco de dados
    animal_editado = db.session.query(Animal).get(animal.id)
    assert animal_editado.nome == 'Novo Nome'
    assert animal_editado.idade == 5
    assert animal_editado.descricao == 'Descrição atualizada'
    assert animal_editado.especie == 'Gato'
    assert animal_editado.porte == 'Pequeno'
    assert animal_editado.sexo == 'Fêmea'
    assert animal_editado.raca == 'Persa'

def test_editar_animal_campos_vazios(test_client):
    # Dados de exemplo para editar um animal com campos vazios
    dados_editados = {
        'nome': True,
        'idade': '',
        'descricao': ''
    }

    # Fazer uma solicitação para editar o animal
    response = test_client.post('/editar_animal/1', data=dados_editados, follow_redirects=True)

    # Verificar se a mensagem de erro é retornada
    assert response.status_code == 304
