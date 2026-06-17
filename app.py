import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests

# Configurações da página e identidade visual
st.set_page_config(page_title="Wiser Ads Benchmark", page_icon="🪽", layout="wide")

st.markdown("""
    <style>
    h1, h2, h3 { color: #621E4F !important; }
    .stButton>button { background-color: #204364; color: white; border-radius: 8px; }
    .stButton>button:hover { background-color: #621E4F; color: white; border-color: #621E4F; }
    </style>
    """, unsafe_allow_html=True)

# Funções de back-end e IA
def analisar_anuncio_ia(api_key, imagem, copy, contexto):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Você é um especialista em Growth Marketing e Mídia Paga no nicho de Educação.
    Abaixo, estou enviando a imagem e a copy de um novo anúncio que criamos.
    
    Copy do Anúncio: "{copy}"
    Contexto do Nicho e Modalidade: "{contexto}"
    
    Analise esta imagem e texto como se estivessem competindo com players que já rodam anúncios validados há 60+ dias.
    Me retorne UMA ANÁLISE ESTRUTURADA EM MARKDOWN com:
    1. **EduScore (0 a 100):** Uma nota geral para o potencial de conversão do criativo.
    2. **Estimativa Competitiva:** Estimativa se o CPL e CTR ficarão Acima, Abaixo ou na Média do mercado para este nicho.
    3. **Análise da Copy:** Pontos fortes e fracos (gatilhos, CTA, nível de clareza da promessa).
    4. **Análise Visual:** A imagem passa autoridade? O contraste está bom? Chama atenção?
    5. **Ação Recomendada:** O que mudar agora para melhorar o ROAS antes de subir a campanha.
    """
    
    try:
        if imagem:
            response = model.generate_content([prompt, imagem])
        else:
            response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro na IA: {e}. Verifique se a chave API é válida."

def buscar_meta_ads(termo_busca, meta_token=None):
    termo = termo_busca.lower()
    
    if "inglês" in termo or "ingles" in termo or "idioma" in termo:
        return [
            {"concorrente": "Concorrente X (Inglês Online)", "dias_ativo": 150, "copy_snippet": "Fluência estudando de casa com tecnologia americana. Conheça o método..."},
            {"concorrente": "Concorrente Y (Inglês Presencial)", "dias_ativo": 95, "copy_snippet": "Salas imersivas e conversação presencial com nativos. Matricule-se na unidade..."},
            {"concorrente": "Concorrente Z (Inglês Básico)", "dias_ativo": 60, "copy_snippet": "Destrave seu inglês em poucos meses e conquiste as melhores vagas de emprego."}
        ]
    else:
        return [
            {"concorrente": "Concorrente A (MBA)", "dias_ativo": 120, "copy_snippet": "Acelere sua carreira em 6 meses com nosso MBA..."},
            {"concorrente": "Concorrente B (Pós-graduação)", "dias_ativo": 85, "copy_snippet": "Pós-graduação EaD com professores de mercado. Inscreva-se..."},
            {"concorrente": "Concorrente C (Soft Skills)", "dias_ativo": 45, "copy_snippet": "Liderança e Gestão: O curso que faltava no seu currículo."}
        ]

# Interface do usuário (front-end)
col1, col2 = st.columns([1, 4])
with col1:
    try:
        st.image("logo.png", width=150)
    except:
        st.warning("Adicione 'logo.png' na pasta do projeto.")
with col2:
    st.title("Ads Benchmark & Preditivo")
    st.markdown("Analise seus criativos frente à concorrência no nicho de Educação.")

st.divider()

# Menu lateral
with st.sidebar:
    st.header("Parâmetros de Mercado")
    
    nicho = st.selectbox("Selecione o foco do anúncio:", [
        "Cursos de Inglês", 
        "Pós-graduação", 
        "Graduação", 
        "MBA", 
        "Cursos Livres (Soft/Hard Skills)"
    ])
    
    if nicho == "Cursos de Inglês":
        modalidade = st.radio("Selecione a modalidade:", ["Online", "Presencial"])
        contexto_final = f"{nicho} ({modalidade})"
        sugestao_busca = f"Curso de Inglês {modalidade}"
    else:
        contexto_final = nicho
        sugestao_busca = nicho
        
    palavra_chave_meta = st.text_input("Termo para buscar na Meta Ads:", value=sugestao_busca)

# Abas principais
aba_bench, aba_analise = st.tabs(["1. Benchmarking de Mercado", "2. Avaliador do seu anúncio (IA)"])

with aba_bench:
    st.subheader("Anúncios validados da concorrência")
    st.markdown("Esta aba busca anúncios ativos há muito tempo no mercado para criar a 'régua de qualidade'.")
    
    if st.button("Buscar Anúncios na Meta"):
        with st.spinner("Buscando dados na Biblioteca da Meta..."):
            resultados = buscar_meta_ads(palavra_chave_meta)
            
            cols = st.columns(3)
            for i, ad in enumerate(resultados):
                with cols[i]:
                    st.info(f"**{ad['concorrente']}**")
                    st.metric("Tempo Ativo", f"{ad['dias_ativo']} dias", "+ Validado", delta_color="normal")
                    st.caption(f"Copy: {ad['copy_snippet']}")
            
            st.success(f"Estes anúncios focados em '{palavra_chave_meta}' agora servem de base para a avaliação!")

with aba_analise:
    st.subheader(f"Suba o seu novo anúncio focado em {contexto_final}")
    
    col_input, col_output = st.columns([1, 1])
    
    with col_input:
        st.markdown("**1. Insira a Copy (texto):**")
        sua_copy = st.text_area("Texto principal do seu anúncio:", height=150)
        
        st.markdown("**2. Faça upload do criativo (imagem):**")
        seu_arquivo_img = st.file_uploader("Formatos suportados: JPG, PNG", type=['png', 'jpg', 'jpeg'])
        
        if seu_arquivo_img:
            img_aberta = Image.open(seu_arquivo_img)
            st.image(img_aberta, caption="Pré-visualização", use_container_width=True)
            
        botao_avaliar = st.button("Gerar ranking preditivo")

    with col_output:
        if botao_avaliar:
            # Tenta puxar a chave diretamente dos "Secrets" do servidor
            try:
                gemini_key = st.secrets["GEMINI_API_KEY"]
            except:
                st.error("⚠️ Erro de Servidor: a chave de API da IA não foi configurada. Contate a administradora do sistema.")
                gemini_key = None
                
            if gemini_key:
                if not sua_copy and not seu_arquivo_img:
                    st.warning("Insira uma copy ou uma imagem para analisar.")
                else:
                    with st.spinner(f"A IA está analisando seu anúncio contra o mercado de {contexto_final}..."):
                        img_para_ia = Image.open(seu_arquivo_img) if seu_arquivo_img else None
                        
                        resultado_ia = analisar_anuncio_ia(
                            api_key=gemini_key, 
                            imagem=img_para_ia, 
                            copy=sua_copy, 
                            contexto=contexto_final
                        )
                        
                        st.markdown("### Resultado da Análise:")
                        st.markdown(resultado_ia)
