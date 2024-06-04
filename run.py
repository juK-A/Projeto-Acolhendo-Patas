from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from firebase_admin import credentials
from flask import send_from_directory
from sqlalchemy.orm import relationship
from firebase_admin import firestore
from firebase_admin import auth
from flask_wtf.csrf import CSRFProtect
import re
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import storage
from flask_wtf.csrf import generate_csrf
import requests
import os

# Inicializar o Firebase Admin SDK
cred = credentials.Certificate('acolhendo-patas-firebase-adminsdk-vrvnn-1e78ac2471.json')
firebase_admin.initialize_app(cred, {'storageBucket': 'acolhendo-patas.appspot.com'})

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cadastro.db'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
app.secret_key = '2029240f6d1128be89ddc32729463129'  # Defina uma chave secreta para utilizar a sessão
db = SQLAlchemy(app)
db_firestore = firestore.client()
load_dotenv()

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    uid = db.Column(db.String(128), nullable=False, unique=True)
    nome_capitalizado = db.Column(db.String(100), nullable=False)
    endereco = db.relationship('Endereco', backref='usuario', uselist=False)
    animais = db.relationship('Animal', backref='usuario', lazy='dynamic')

    @staticmethod
    def capitalizar_nome(nome):
        return nome.capitalize()

    def __init__(self, nome, email, uid):
        self.nome = nome
        self.email = email
        self.uid = uid
        self.nome_capitalizado = self.capitalizar_nome(nome)

class Endereco(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(2), nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    cep = db.Column(db.String(10), nullable=False)
    cidade= db.Column(db.String(30), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

class Imagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(5000), nullable=False)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)

class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    especie = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    porte = db.Column(db.Text, nullable=False)
    sexo = db.Column(db.Text, nullable=False)
    raca = db.Column(db.Text, nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    imagens = db.relationship('Imagem', backref='animal', lazy=True)

@app.route('/css/<path:filename>')
def css(filename):
    diretorio_css = os.path.join(app.root_path, 'templates', 'css')
    return send_from_directory(diretorio_css, filename)

@app.route('/imagens/<path:filename>')
def imagens(filename):
    diretorio_imagens = os.path.join(app.root_path, 'templates', 'img')
    return send_from_directory(diretorio_imagens, filename)

@app.route('/js/<path:filename>')
def js(filename):
    diretorio_js = os.path.join(app.root_path, 'templates', 'js')
    return send_from_directory(diretorio_js, filename)

@app.route('/detalhes_animal/<int:animal_id>')
def detalhes_animal(animal_id):
    # Verificar se o usuário está logado
    if 'uid' in session:
        uid = session['uid']
        usuario = Usuario.query.filter_by(uid=uid).first()
        if usuario:
            nome_usuario = usuario.nome_capitalizado
            
            # Buscar o animal no banco de dados pelo ID
            animal = Animal.query.get(animal_id)

            # Verificar se o animal existe
            if not animal:
                return render_template('404.html'), 404  # Retorna uma página de erro 404 se o animal não existir

            endereco = Endereco.query.filter_by(usuario_id=animal.usuario_id).first()
            # Verificar se o usuário logado é o proprietário do animal
            proprietario = (animal.usuario_id == usuario.id)

            # Renderizar a página de detalhes do animal, passando a lista de imagens do animal
            return render_template('detalhes_animal.html', animal=animal, nome_usuario=nome_usuario, proprietario=proprietario, endereco=endereco, usuario=usuario)
        else:
            flash("Usuário não encontrado", "danger")
            return redirect(url_for('login'))
    else:
        flash("Por favor, faça o login para acessar esta página", "warning")
        return redirect(url_for('login'))



@app.route('/queroadotar', methods=['GET', 'POST'])
def queroadotar():
    if 'uid' in session:
        uid = session['uid']
        usuario = Usuario.query.filter_by(uid=uid).first()
        if usuario:
            nome_usuario = usuario.nome_capitalizado

            # Obter os filtros da solicitação
            especie = request.args.get('especie', default='', type=str)
            sexo = request.args.get('sexo', default='', type=str)
            porte = request.args.get('porte', default='', type=str)

            # Construir a URL da API com os parâmetros de filtro
            url = url_for('api_get_animais', especie=especie, sexo=sexo, porte=porte, _external=True)

            # Fazer a solicitação à API
            response = requests.get(url)
            data = response.json()

            animal_info = []
            for item in data:
                animal = Animal.query.get(item['id'])
                imagem = Imagem.query.filter_by(animal_id=animal.id).first()
                owner = Usuario.query.filter_by(id=animal.usuario_id).first()
                endereco = Endereco.query.filter_by(usuario_id=owner.id).first()
                animal_info.append({
                    'animal': animal,
                    'owner': owner,
                    'endereco': endereco,
                    'imagem': imagem
                })

            return render_template('queroAdotar.html', nome_usuario=nome_usuario, animal_info=animal_info, usuario=usuario)
    return redirect(url_for('login'))

@app.route('/processoadocao', methods=['GET', 'POST'])
def processoadocao():
    if 'uid' in session:
        uid = session['uid']
        usuario = Usuario.query.filter_by(uid=uid).first()
    else:
        flash("Por favor, faça o login para acessar esta página", "warning")
        return redirect(url_for('login'))
    if usuario:
            nome_usuario = usuario.nome_capitalizado
            return render_template('processo-adocao.html', nome_usuario=nome_usuario, usuario=usuario)

@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'uid' in session:
        uid = session['uid']
        usuario = Usuario.query.filter_by(uid=uid).first()
        if usuario:
            nome_usuario = usuario.nome_capitalizado
            return render_template('index.html', nome_usuario=nome_usuario, usuario=usuario)
        else:
            flash("Usuário não encontrado", "danger")
            return redirect(url_for('login'))
    else:
        flash("Por favor, faça o login para acessar esta página", "warning")
        return redirect(url_for('login'))

def verify_user_password(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        user_info = response.json()
        return user_info  # Contém o token de ID e outras informações do usuário
    else:
        return None

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if 'uid' in session:
        uid = session['uid']
        usuario = Usuario.query.filter_by(uid=uid).first()
        if usuario:
            nome_usuario = usuario.nome_capitalizado
            return render_template('cadastro.html', nome_usuario=nome_usuario)
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        estado = request.form['estado']
        endereco = request.form['endereco']
        cep = request.form['cep']
        cidade = request.form['cidade']
        telefone = request.form['telefone']
        
        if not any([nome, email, senha, estado, endereco, cep, cidade, telefone]):
            flash("Todos os campos são obrigatórios.", "danger")
            return redirect(url_for('cadastro'))

        
        if email and not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            flash("Formato de email inválido.", "danger")
            return redirect(url_for('cadastro'))

        try:
            user = auth.create_user(email=email, password=senha)
            uid = user.uid
        except firebase_admin._auth_utils.EmailAlreadyExistsError:
            flash("O email fornecido já está em uso.", "danger")
            return redirect(url_for('cadastro'))

        # Criar novo usuário no banco de dados local
        novo_usuario = Usuario(nome=nome, email=email, uid=uid)
        db.session.add(novo_usuario)
        db.session.commit()

        # Criar novo endereço
        novo_endereco = Endereco(estado=estado, endereco=endereco, cep=cep, telefone=telefone, usuario=novo_usuario, cidade=cidade)
        db.session.add(novo_endereco)
        db.session.commit()
        flash("Usuario cadastrado com sucesso.", "success")
        return redirect(url_for('cadastro'))
    
    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        user_info = verify_user_password(email, senha)
        if user_info:
            uid = user_info['localId']
            id_token = user_info['idToken']

            # Obter informações do usuário a partir do banco de dados local
            usuario = Usuario.query.filter_by(uid=uid).first()
            if usuario:
                # Salvar informações do usuário na sessão
                session['usuario_id'] = usuario.id
                session['uid'] = uid
                session['id_token'] = id_token
                flash("Logado com sucesso!", "success")
                return redirect(url_for('index'))
            else:
                flash("Usuário não encontrado", "danger")
        else:
            flash("Credenciais inválidas.", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Remover todas as variáveis de sessão
    return redirect(url_for('login'))

def capitalizar_nome(nome):
    return nome.capitalize()


@app.route('/editar_usuario', methods=['GET', 'POST'])
def editar_usuario():
    if 'uid' in session:
        uid = session['uid']
        usuario = Usuario.query.filter_by(uid=uid).first()
        endereco = Endereco.query.filter_by(usuario_id=usuario.id).first()
        if usuario:
            nome_usuario = usuario.nome_capitalizado  # Aqui você obtém o nome do usuário logado
            if request.method == 'POST':
                # Obter os novos dados do formulário
                novo_nome = request.form['nome']
                novo_email = request.form['email']
                nova_senha = request.form['senha']
                novo_telefone = request.form['telefone']
                novo_estado = request.form['estado']
                novo_endereco = request.form['endereco']
                novo_cep = request.form['cep']
                nova_cidade = request.form['cidade']

                # Atualizar os dados do usuário no banco de dados
                usuario.nome = novo_nome
                usuario.email = novo_email
                usuario.nome_capitalizado = novo_nome.capitalize()
                endereco.estado = novo_estado
                endereco.endereco = novo_endereco
                endereco.cep = novo_cep
                endereco.telefone = novo_telefone
                endereco.cidade = nova_cidade
                db.session.commit()
                flash("Dados do usuário atualizados com sucesso!", "success")

                # Atualizar o nome de usuário na sessão
                session['nome_usuario'] = novo_nome

                # Verificar se uma nova senha foi fornecida
                if nova_senha:
                    try:
                        # Atualizar a senha do usuário no Firebase Authentication
                        user = auth.update_user(
                            uid,
                            email=novo_email,
                            password=nova_senha
                        )
                        print('Senha do usuário atualizada no Firebase:', user)
                    except Exception as e:
                        print('Erro ao atualizar a senha do usuário no Firebase:', str(e))

                return redirect(url_for('meus_animais'))  # Redirecionar para a página inicial ou outra página
            else:
                # Exibir o formulário de edição com os dados atuais do usuário preenchidos
                return render_template('editar_usuario.html', nome_usuario=nome_usuario, usuario=usuario, endereco=endereco)
        else:
            flash("Usuário não encontrado", "danger")
            return redirect(url_for('login'))
    else:
        flash("Por favor, faça o login para acessar esta página", "warning")
        return redirect(url_for('login'))

    
def atualizar_dados_usuario_firebase(uid, novo_nome, novo_email):
    try:
        # Atualize os dados do usuário no Firebase Authentication
        user = auth.update_user(
            uid,
            display_name=novo_nome,
            email=novo_email
        )
        
        print('Dados do usuário atualizados no Firebase:', user)
    except Exception as e:
        print('Erro ao atualizar os dados do usuário no Firebase:', str(e))

@app.route('/cadastro_pet', methods=['GET', 'POST'])
def cadastro_pet():
    if 'uid' in session:
        uid = session['uid']
        usuario = Usuario.query.filter_by(uid=uid).first()
        if usuario:
            nome_usuario = usuario.nome_capitalizado
            usuario_id = usuario.id
        else:
            flash("Usuário não encontrado", "danger")
            return redirect(url_for('login'))
    else:
        flash("Você não está logado!", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Obter dados do formulário
        nome = capitalizar_nome(request.form.get('nomePet'))
        especie = request.form.get('especie')
        porte = request.form.get('porte')
        sexo = request.form.get('sexo')
        raca = request.form.get('raca')
        descricao = request.form.get('descricao')
        idade = request.form.get('idade')

        # Verificar se a raça é indefinida
        if request.form.get('undefinedBreed'):
            raca = 'SRD'  # Define a raça como SRD

        # Verificar se a idade é indefinida
        if request.form.get('undefinedAge'):
            idade = 'Idade desconhecida'  # Define a idade como Desconhecida

        # Verificar se todos os campos obrigatórios foram preenchidos
        if not nome or not especie or not porte or not sexo or not raca or not descricao or not idade:
            flash("Todos os campos são obrigatórios.", "danger")
            return redirect(url_for('cadastro_pet'))

        # Verificar se o usuário existe
        usuario = Usuario.query.get(usuario_id)
        if usuario:
            # Criar novo animal associado ao usuário
            animal = Animal(nome=nome, especie=especie, porte=porte, sexo=sexo, descricao=descricao, raca=raca, idade=idade, usuario=usuario)

            # Lidar com o upload da imagem
            imagem = request.files.get('imagem')
            if imagem and imagem.filename != '':
                # Verificar a extensão do arquivo
                allowed_extensions = ['.png', '.jpg', '.jpeg']
                extension = os.path.splitext(imagem.filename)[1].lower()
                if extension not in allowed_extensions:
                    flash("Apenas arquivos PNG ou JPG são permitidos.", "danger")
                    return redirect(url_for('cadastro_pet'))

                # Enviar a imagem para o Firebase Storage
                filename = secure_filename(imagem.filename)
                bucket_name = "acolhendo-patas.appspot.com"    
                bucket = storage.bucket(bucket_name)
                blob = bucket.blob(filename)
                blob.upload_from_file(imagem)
                image_url = blob.public_url
                blob.generate_signed_url(expiration=3600)
                blob.make_public()

                # Criar novo objeto Imagem com a URL da imagem
                imagem_obj = Imagem(url=image_url, animal=animal)

                # Adicionar o objeto Imagem à lista de imagens do animal
                animal.imagens.append(imagem_obj)

            try:
                db.session.add(animal)
                db.session.commit()
                flash("Animal cadastrado com sucesso!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Erro ao cadastrar o animal: {str(e)}", "danger")
        else:
            flash("Usuário não encontrado", "danger")
            return redirect(url_for('login'))

        return redirect(url_for('cadastro_pet'))

    return render_template('cadastro_pet.html', nome_usuario=nome_usuario, usuario=usuario)

@app.route('/meus_animais')
def meus_animais():
    if 'uid' in session:
        uid = session['uid']
        usuario = Usuario.query.filter_by(uid=uid).first()
        if usuario:
            nome_usuario = usuario.nome_capitalizado
            animais = Animal.query.filter_by(usuario_id=usuario.id).all()
            animal_info = []
            for animal in animais:
                imagem = Imagem.query.filter_by(animal_id=animal.id).first()
                animal_info.append({
                    'animal': animal,
                    'imagem': imagem
                })

            # Verificar se há uma mensagem de sucesso na sessão
            success_message = session.pop('success_message', None)
            if success_message:
                flash(success_message, "success")

            return render_template('meusanimais.html', nome_usuario=nome_usuario, animal_info=animal_info, usuario=usuario)
    return redirect(url_for('login'))

@app.route('/editar_animal/<int:animal_id>', methods=['GET', 'POST'])
def editar_animal(animal_id):
    animal = Animal.query.get_or_404(animal_id)
    if 'uid' in session:
        uid = session['uid']
        usuario = Usuario.query.filter_by(uid=uid).first()
        if usuario and animal.usuario_id == usuario.id:
            nome_usuario = usuario.nome_capitalizado

            if request.method == 'POST':
                animal.nome = request.form.get('nomePet')
                animal.especie = request.form.get('especie')
                animal.raca = request.form.get('raca')
                animal.porte = request.form.get('porte')
                animal.sexo = request.form.get('sexo')
                animal.descricao = request.form.get('descricao')
                animal.idade = request.form.get('idade')

                imagem = request.files.get('imagem')
                if imagem and imagem.filename != '':
                    # Verificar a extensão do arquivo
                    allowed_extensions = ['.png', '.jpg', '.jpeg']
                    extension = os.path.splitext(imagem.filename)[1].lower()
                    if extension not in allowed_extensions:
                        flash("Apenas arquivos PNG ou JPG são permitidos.", "danger")
                        return redirect(url_for('editar_animal', animal_id=animal.id))

                    filename = secure_filename(imagem.filename)
                    bucket_name = "acolhendo-patas.appspot.com"
                    bucket = storage.bucket(bucket_name)
                    blob = bucket.blob(filename)
                    blob.upload_from_file(imagem)
                    image_url = blob.public_url
                    blob.generate_signed_url(expiration=3600)
                    blob.make_public()

                    imagem_obj = Imagem.query.filter_by(animal_id=animal.id).first()
                    if imagem_obj:
                        imagem_obj.url = image_url
                    else:
                        nova_imagem = Imagem(url=image_url, animal=animal)
                        animal.imagens.append(nova_imagem)

                # Verificar se todos os campos obrigatórios foram preenchidos
                if not animal.nome or not animal.especie or not animal.porte or not animal.sexo or not animal.raca or not animal.descricao or not animal.idade:
                    flash("Todos os campos devem ser preenchidos.", "danger")
                    return redirect(url_for('editar_animal', animal_id=animal.id))

                try:
                    db.session.commit()
                    flash("Animal atualizado com sucesso!", "success")
                    return redirect(url_for('meus_animais'))
                except Exception as e:
                    db.session.rollback()
                    flash(f"Erro ao atualizar o animal: {str(e)}", "danger")

            return render_template('editar_animal.html', animal=animal, nome_usuario=nome_usuario, usuario=usuario)
        else:
            flash("Você não tem permissão para editar este animal.", "danger")
            return redirect(url_for('meus_animais'))
    else:
        flash("Você não está logado!", "warning")
        return redirect(url_for('login'))

@app.route('/deletar_animal/<int:animal_id>', methods=['POST'])
def deletar_animal(animal_id):
    animal = Animal.query.get_or_404(animal_id)
    if 'uid' in session and animal.usuario.uid == session['uid']:
        try:
            # Excluir as imagens associadas ao animal
            for imagem in animal.imagens:
                db.session.delete(imagem)

            db.session.delete(animal)
            db.session.commit()
            # Armazenar a mensagem de sucesso na sessão
            session['success_message'] = "Animal deletado com sucesso!"
            return redirect(url_for('meus_animais'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao deletar o animal: {str(e)}", "danger")
            return redirect(url_for('meus_animais'))
    else:
        flash("Você não tem permissão para deletar este animal.", "danger")
        return redirect(url_for('meus_animais'))




@app.route('/api/animais', methods=['GET'])
def api_get_animais():
    especie = request.args.get('especie', default='', type=str)
    sexo = request.args.get('sexo', default='', type=str)
    porte = request.args.get('porte', default='', type=str)

    query = Animal.query

    if especie:
        query = query.filter(Animal.especie == especie)
    if sexo:
        query = query.filter(Animal.sexo == sexo)
    if porte:
        query = query.filter(Animal.porte == porte)

    animais = query.all()

    results = []
    for animal in animais:
        imagem = Imagem.query.filter_by(animal_id=animal.id).first()
        results.append({
            'id': animal.id,
            'nome': animal.nome,
            'especie': animal.especie,
            'descricao': animal.descricao,
            'raca': animal.raca,
            'idade': animal.idade,
            'image_url': imagem.url if imagem else None
        })
    return jsonify(results), 200

@app.route('/api/usuario/<int:usuario_id>/animais', methods=['GET'])
def api_get_animais_por_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    animais = Animal.query.filter_by(usuario_id=usuario.id).all()
    results = []
    for animal in animais:
        imagem = Imagem.query.filter_by(animal_id=animal.id).first()
        results.append({
            'id': animal.id,
            'nome': animal.nome,
            'especie': animal.especie,
            'descricao': animal.descricao,
            'raca': animal.raca,
            'idade': animal.idade,
            'image_url': imagem.url if imagem else None
        })
    return jsonify(results), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
