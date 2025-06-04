from flask import Flask, render_template, request, redirect, url_for, session
import json

app = Flask(__name__)
app.secret_key = 'segredo'

def carregar_usuarios():
    try:
        with open("usuarios.json", "r") as f:
            return json.load(f)
    except:
        return []

@app.route('/')
def inicio():
    return render_template("inicio.html")

@app.route('/inicio')
def redirect_inicio():
    return redirect(url_for('inicio'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuarios = carregar_usuarios()
        usuario = request.form['usuario']
        senha = request.form['senha']
        for u in usuarios:
            if u['usuario'] == usuario and u['senha'] == senha:
                session['usuario'] = usuario
                session['tipo'] = u['tipo']
                return redirect(url_for('painel'))
        return render_template("login.html", erro="Usuário ou senha incorretos")
    return render_template("login.html")

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        usuario = request.form['usuario'].strip()
        senha = request.form['senha']
        tipo = request.form['tipo']

        if len(usuario) == 0:
            return render_template("cadastro.html", erro="Usuário não pode ser vazio.")
        if len(senha) < 6:
            return render_template("cadastro.html", erro="A senha deve ter no mínimo 6 caracteres.")

        usuarios = carregar_usuarios()
        for u in usuarios:
            if u['usuario'].lower() == usuario.lower():
                return render_template("cadastro.html", erro="Usuário já existe.")

        usuarios.append({'usuario': usuario, 'senha': senha, 'tipo': tipo})
        with open("usuarios.json", "w") as f:
            json.dump(usuarios, f, indent=2)
        return redirect(url_for('login'))

    return render_template("cadastro.html")

@app.route('/painel')
def painel():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if session['tipo'] == 'admin':
        usuarios = carregar_usuarios()
        alunos = [u['usuario'] for u in usuarios if u['tipo'] == 'aluno']
        return render_template("painel_admin.html", usuario=session['usuario'], alunos=alunos)
    else:
        return redirect(url_for('mostrar_treinos'))

@app.route('/adicionar_treino', methods=['POST'])
def adicionar_treino():
    if session.get('tipo') != 'admin':
        return redirect(url_for('login'))

    aluno = request.form['aluno']
    dia = request.form['dia']
    # Recebe listas de campos duplicados
    exercicios_nome = request.form.getlist('exercicio_nome')
    exercicios_video = request.form.getlist('exercicio_video')
    exercicios_repeticoes = request.form.getlist('exercicio_repeticoes')

    exercicios = []
    for i in range(len(exercicios_nome)):
        exercicios.append({
            "dia": dia,
            "nome": exercicios_nome[i],
            "video": exercicios_video[i],
            "repeticoes": exercicios_repeticoes[i]
        })

    try:
        with open("treinos_alunos.json", "r") as f:
            treinos_alunos = json.load(f)
    except:
        treinos_alunos = {}

    if aluno not in treinos_alunos:
        treinos_alunos[aluno] = []

    treinos_alunos[aluno].extend(exercicios)

    with open("treinos_alunos.json", "w") as f:
        json.dump(treinos_alunos, f, indent=2)

    return redirect(url_for('painel'))

@app.route('/treinos')
def mostrar_treinos():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    usuario = session['usuario']

    try:
        with open("treinos_alunos.json", "r") as f:
            treinos_por_usuario = json.load(f)
    except:
        treinos_por_usuario = {}

    treinos_personalizados = treinos_por_usuario.get(usuario, [])
    return render_template('treinos.html', treinos_personalizados=treinos_personalizados)

@app.route('/treinos_predefinidos')
def ver_predefinidos():
    from treino_predefinido import treinos_prontos
    return render_template('treinos_predefinidos.html', treinos=treinos_prontos)

@app.route('/editar_dados', methods=['GET', 'POST'])
def editar_dados():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    usuarios = carregar_usuarios()
    usuario_atual = session['usuario']
    user = next((u for u in usuarios if u['usuario'] == usuario_atual), None)

    if request.method == 'POST':
        nova_senha = request.form['senha']
        if len(nova_senha) >= 6:
            user['senha'] = nova_senha
            with open("usuarios.json", "w") as f:
                json.dump(usuarios, f, indent=2)
            return redirect(url_for('mostrar_treinos'))
        else:
            return render_template("editar_dados.html", erro="Senha deve ter ao menos 6 caracteres.", usuario=usuario_atual)

    return render_template("editar_dados.html", usuario=usuario_atual)

# ADICIONE ESTA NOVA ROTA AQUI:
@app.route('/dados_pessoais', methods=['GET', 'POST'])
def dados_pessoais():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    usuarios = carregar_usuarios()
    usuario_atual = next((u for u in usuarios if u['usuario'] == session['usuario']), None)
    
    if request.method == 'POST':
        # Atualizar dados pessoais
        if 'celular' not in usuario_atual:
            usuario_atual['celular'] = ''
        if 'endereco' not in usuario_atual:
            usuario_atual['endereco'] = ''
        if 'idade' not in usuario_atual:
            usuario_atual['idade'] = ''
        if 'peso' not in usuario_atual:
            usuario_atual['peso'] = ''
        if 'altura' not in usuario_atual:
            usuario_atual['altura'] = ''
            
        usuario_atual['celular'] = request.form.get('celular', '')
        usuario_atual['endereco'] = request.form.get('endereco', '')
        usuario_atual['idade'] = request.form.get('idade', '')
        usuario_atual['peso'] = request.form.get('peso', '')
        usuario_atual['altura'] = request.form.get('altura', '')
        
        # Calcular IMC se peso e altura estiverem preenchidos
        if usuario_atual['peso'] and usuario_atual['altura']:
            try:
                peso = float(usuario_atual['peso'])
                altura = float(usuario_atual['altura'])
                usuario_atual['imc'] = round(peso / (altura ** 2), 2)
            except:
                usuario_atual['imc'] = None
        else:
            usuario_atual['imc'] = None
        
        with open("usuarios.json", "w") as f:
            json.dump(usuarios, f, indent=2)
        
        return redirect(url_for('dados_pessoais'))
    
    return render_template('dado_aluno.html', usuario=usuario_atual)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')