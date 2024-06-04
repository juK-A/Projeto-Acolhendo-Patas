import pytest
from run import Animal, app


def test_cadastro_pet_sucesso(test_client, authenticated_client):
    # Dados de teste válidos
    dados_pet = {
        'nomePet': 'Tobby',
        'especie': 'Cachorro',
        'porte': 'Pequeno',
        'sexo': 'Macho',
        'raca': 'Poodle',
        'descricao': 'Cachorro muito amigável',
        'idade': '3'
    }

    # Enviar a requisição POST para a rota /cadastro_pet
    response = authenticated_client.post('/cadastro_pet', data=dados_pet, follow_redirects=True)

    # Verificar se o animal foi criado corretamente
    animal = Animal.query.filter_by(nome=dados_pet['nomePet']).first()
    assert animal is not None
    assert response.status_code == 200
    assert b'Animal cadastrado com sucesso!' in response.data

def test_cadastro_pet_campos_vazios(test_client, authenticated_client):
    # Dados de teste com campos vazios
    dados_pet = {
        'nomePet': '',
        'especie': '',
        'porte': '',
        'sexo': '',
        'raca': '',
        'descricao': '',
        'idade': ''
    }

    # Enviar a requisição POST para a rota /cadastro_pet
    response = authenticated_client.post('/cadastro_pet', data=dados_pet, follow_redirects=True)

    # Verificar se ocorreram erros de campos vazios
    assert b'Todos os campos s\xc3\xa3o obrigat\xc3\xb3rios.' in response.data

# def test_cadastro_pet_idade_invalida(test_client, authenticated_client):
#     # Dados de teste com idade inválida
#     dados_pet = {
#         'nomePet': 'Tobby',
#         'especie': 'Cachorro',
#         'porte': 'Pequeno',
#         'sexo': 'Macho',
#         'raca': 'Poodle',
#         'descricao': 'Cachorro muito amigável',
#         'idade': 'abc'
#     }

#     # Enviar a requisição POST para a rota /cadastro_pet
#     response = authenticated_client.post('/cadastro_pet', data=dados_pet, follow_redirects=True)

#     # Verificar se ocorreu um erro de idade inválida
#     assert b'A idade deve ser um n\xc3\xbamero inteiro v\xc3\xa1lido.' in response.data
