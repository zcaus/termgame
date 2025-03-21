import streamlit as st
import random
import requests
import unicodedata

# Configura a página para o modo wide e define o título da aba
st.set_page_config(page_title="TERMO DO ZCAUS", layout="wide")

# --- Funções Auxiliares ---
def remover_acentos(texto):
    """Remove acentos de uma string."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def calcular_feedback(guess, secret):
    """
    Calcula o feedback (lista de "green", "yellow" ou "gray") para um palpite,
    respeitando a contagem de letras na palavra secreta.
    As comparações são feitas ignorando acentos.
    """
    norm_secret = remover_acentos(secret)
    norm_guess = remover_acentos(guess)
    feedback = ["gray"] * len(norm_guess)
    contagem = {}
    for letra in norm_secret:
        contagem[letra] = contagem.get(letra, 0) + 1
    # Primeira passagem: acertos na posição correta
    for i, letra in enumerate(norm_guess):
        if letra == norm_secret[i]:
            feedback[i] = "green"
            contagem[letra] -= 1
    # Segunda passagem: letras fora da posição correta
    for i, letra in enumerate(norm_guess):
        if feedback[i] != "green" and contagem.get(letra, 0) > 0:
            feedback[i] = "yellow"
            contagem[letra] -= 1
    return feedback

def render_guess(guess, secret):
    """Gera o HTML para exibir o palpite com quadrados coloridos."""
    feedback = calcular_feedback(guess, secret)
    letter_boxes = ""
    for i, letra in enumerate(guess):
        classe = feedback[i]
        letter_boxes += f'<span class="letter-box {classe}">{letra.upper()}</span>'
    return letter_boxes

def validar_palavra(palavra):
    """Valida se a palavra existe usando a API do Dicionário Aberto."""
    url = f"https://api.dicionario-aberto.net/word/{palavra}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list) and 'word' in data[0]:
                palavra_api = data[0]['word'].lower()
                if remover_acentos(palavra_api) == remover_acentos(palavra):
                    return True
                else:
                    return True  # Aceitamos mesmo que não seja exata.
            else:
                return False
        else:
            return False
    except Exception as e:
        st.error("Erro ao conectar com a API de validação.")
        return False

# --- Parâmetros do Jogo ---
tamanho_palavra = 5

def definir_limite(modo):
    if modo == "Simples":
        return 6
    elif modo == "Dueto":
        return 7
    else:
        return 9

# --- Lista Interna de Palavras Ampliada ---
palavras_internas = [
    'amigo', 'corpo', 'tarde', 'noite', 'mundo', 'sabor', 'tempo', 'festa',
    'chave', 'sonho', 'brisa', 'verde', 'firme', 'grato', 'letra', 'plena',
    'feliz', 'certo', 'sorte', 'viver', 'magia', 'olhar', 'verbo', 'gusto',
    'suave', 'breve', 'claro', 'manso', 'nobre', 'justo', 'forte', 'pilar',
    'grama', 'palco', 'prado', 'torre', 'porto', 'combo', 'rosto', 'canto',
    'bando'
]

# Filtra as palavras que tenham exatamente 5 letras após remover acentos
palavras_filtradas = [p for p in palavras_internas if len(remover_acentos(p)) == tamanho_palavra]
if not palavras_filtradas:
    st.error(f"Não há palavras com {tamanho_palavra} letras disponíveis.")
    st.stop()

# --- Seleção de Modo de Jogo ---
def mudar_modo():
    st.session_state["modo"] = st.session_state["_modo_select"]
    iniciar_jogo()

if "modo" not in st.session_state:
    st.session_state["modo"] = "Simples"

modo = st.selectbox(
    "Selecione o modo:",
    options=["Simples", "Dueto", "Quarteto"],
    key="_modo_select",
    on_change=mudar_modo
)

# --- Inicialização do Estado da Sessão ---
if st.session_state["modo"] == "Simples":
    num_secrets = 1
elif st.session_state["modo"] == "Dueto":
    num_secrets = 2
else:
    num_secrets = 4

if "palavras_secretas" not in st.session_state:
    if num_secrets > len(palavras_filtradas):
        st.error("Não há palavras suficientes para o modo selecionado sem repetição.")
        st.stop()
    st.session_state["palavras_secretas"] = random.sample(palavras_filtradas, num_secrets)
if "acertos" not in st.session_state:
    st.session_state["acertos"] = [False] * num_secrets
if "tentativas" not in st.session_state:
    st.session_state["tentativas"] = []
if "palpite_input" not in st.session_state:
    st.session_state["palpite_input"] = ""

def iniciar_jogo():
    modo_atual = st.session_state["modo"]
    if modo_atual == "Simples":
        num_secrets = 1
    elif modo_atual == "Dueto":
        num_secrets = 2
    else:
        num_secrets = 4
    if num_secrets > len(palavras_filtradas):
        st.error("Não há palavras suficientes para o modo selecionado sem repetição.")
        st.stop()
    st.session_state["palavras_secretas"] = random.sample(palavras_filtradas, num_secrets)
    st.session_state["acertos"] = [False] * num_secrets
    st.session_state["tentativas"] = []
    st.session_state["palpite_input"] = ""

# --- Layout e Estilos ---
st.title("TERMO DO ZCAUS")

st.markdown("""
<style>
.letter-box {
    display: inline-block;
    width: 50px;
    height: 50px;
    line-height: 50px;
    margin: 2px;
    text-align: center;
    font-size: 24px;
    font-weight: bold;
    border: 2px solid #ccc;
    border-radius: 5px;
}
.letter-box.green {
    background-color: #6aaa64;
    color: white;
    border-color: #6aaa64;
}
.letter-box.yellow {
    background-color: #c9b458;
    color: white;
    border-color: #c9b458;
}
.letter-box.gray {
    background-color: #787c7e;
    color: white;
    border-color: #787c7e;
}
.board {
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# --- Processamento do Palpite ---
def enviar_palpite():
    palpite = st.session_state.palpite_input.lower()
    if len(remover_acentos(palpite)) != tamanho_palavra:
        st.error(f"A palavra deve ter {tamanho_palavra} letras (ignorando acentos)!")
    else:
        if not validar_palavra(palpite):
            st.error("Palavra inválida! Verifique sua ortografia ou tente outra palavra.")
            st.session_state.palpite_input = ""
            return
        feedback_list = []
        for idx, secret in enumerate(st.session_state["palavras_secretas"]):
            if st.session_state["acertos"][idx]:
                html = "".join(f'<span class="letter-box green">{letra.upper()}</span>' for letra in secret)
            else:
                html = render_guess(palpite, secret)
                if remover_acentos(palpite) == remover_acentos(secret):
                    st.session_state["acertos"][idx] = True
            feedback_list.append(html)
        st.session_state["tentativas"].append((palpite, feedback_list))
    st.session_state["palpite_input"] = ""

# --- Exibição das Tentativas ---
st.subheader("Tentativas")
if st.session_state["modo"] == "Simples":
    num_secrets = 1
elif st.session_state["modo"] == "Dueto":
    num_secrets = 2
else:
    num_secrets = 4

for tentativa, feedback_list in st.session_state["tentativas"]:
    cols = st.columns(num_secrets)
    for idx, col in enumerate(cols):
        with col:
            st.markdown(feedback_list[idx], unsafe_allow_html=True)

tentativas_feitas = len(st.session_state["tentativas"])
limite = definir_limite(st.session_state["modo"])
if not all(st.session_state["acertos"]) and tentativas_feitas >= limite:
    st.error("Limite de tentativas atingido!")
    secret_words = " | ".join(secret.upper() for secret in st.session_state["palavras_secretas"])
    st.info(f"As palavras secretas eram: **{secret_words}**")
elif all(st.session_state["acertos"]):
    st.success("Parabéns! Você acertou todas as palavras!")

# --- Campo de Entrada ---
if not all(st.session_state["acertos"]) and tentativas_feitas < limite:
    st.text_input(
        "Digite sua palavra:",
        key="palpite_input",
        max_chars=tamanho_palavra,
        on_change=enviar_palpite
    )

# --- Botão para Reiniciar ---
if st.button("Jogar novamente"):
    iniciar_jogo()
    st.rerun()
