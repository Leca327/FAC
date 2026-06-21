# 👵🩺 CuidaCare - Sistema de Gestão de Cuidados Domiciliares 

## Descrição

O Sistema de Gestão de Cuidados Domiciliares é uma aplicação web desenvolvida para auxiliar famílias e cuidadoras no acompanhamento da rotina de pacientes atendidos em ambiente domiciliar.

O sistema oferece funcionalidades como agenda médica, controle de jornada das cuidadoras, prontuário digital e relatórios de acompanhamento, promovendo maior organização, transparência e segurança no cuidado dos pacientes.

Cada usuário conta ainda com a tela **Meu Perfil**, acessível pelo menu do usuário (canto superior direito), onde pode ver e editar seus dados (nome, e-mail, CPF, telefone, endereço e CEP) e alterar a senha. As etiquetas **Familiar/Cuidador** são exibidas conforme os pacientes em que a pessoa participa.

## 🌐 Tecnologias Utilizadas

**Backend**
- Python 3.12
- Django 5.x
- MySQL (driver PyMySQL)

**Frontend**
- HTML5
- CSS3
- JavaScript

**Ferramentas**
- Git
- GitHub
- Figma
- Trello

## ▶️ Como rodar o projeto localmente

O backend é feito em **Python + Django** e usa **MySQL** (driver PyMySQL).
O passo a passo completo está documentado em dois manuais na raiz do repositório:

- **[MANUAL_INSTALACAO.txt](MANUAL_INSTALACAO.txt)** — instalação inicial (Python 3.12, MySQL, ambiente virtual, dependências e preparação do banco). Faça isto **uma vez**.
- **[MANUAL_CRIANDO_O_BANCO.txt](MANUAL_CRIANDO_O_BANCO.txt)** — passo a passo só do banco: importar o dump `bdcuidacare.sql` **e** rodar as migrações do Django (o `.sql` cria o schema da aplicação, mas as tabelas internas do Django — sessão/login, auth, etc. — são criadas pelo `migrate`).
- **[MANUAL_EXECUCAO.txt](MANUAL_EXECUCAO.txt)** — como subir o servidor no dia a dia e visualizar o site no navegador.

Resumo rápido (após a instalação):

```powershell
cd site
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Depois abra **http://127.0.0.1:8000/** no navegador. Após o login, a tela **Meu Perfil** fica em **http://127.0.0.1:8000/conta/perfil/** (ou pelo menu do usuário, acima de "Sair").

## Integrantes

- ANA CAROLINA DE SOUZA ARAÚJO
- ANGÉLICA LIMA SOARES DE OLIVEIRA
- ANNA CAROLINA MILITÃO DOS SANTOS
- CAMILE PIMENTA MONTEIRO
- DAVI MATOS DOS SANTOS
- FELIPE GABRIEL FERRAZ DOS SANTOS
- JOÃO LUCAS TAVARES DOS SANTOS
- KAMILLE MONTEIRO
- LUCAS RATS FERREIRA
- LETÍCIA DOS REIS PRADO
- RICARDO DOS SANTOS DIAS


