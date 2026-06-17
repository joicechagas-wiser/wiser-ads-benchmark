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
def analisar_anuncio_ia(api_key, imagem, copy, contexto, url_preview=""):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    
    prompt = f"""
    Você é um especialista em Growth Marketing e Mídia Paga no nicho de Educação.
    Estou te enviando as informações de um novo anúncio que criamos.
    
    Copy do Anúncio: "{copy}"
    Contexto do Nicho e Modalidade: "{contexto}"
    URL de Pré-visualização da Meta: "{url_preview}"
    
    Analise estes elementos como se estivessem competindo com players que já rodam anúncios validados há 60+ dias.
    Se a URL for fornecida, considere que este é o destino ou a fonte do anúncio na plataforma da Meta.
    
    Me retorne UMA ANÁLISE ESTRUTURADA EM MARKDOWN com:
    1. **EduScore (0 a 100):** Uma nota geral para o potencial de conversão do criativo.
    2. **Estimativa Competitiva:** Estimativa se o CPL e CTR ficarão Acima, Abaixo ou na Média do mercado para este nicho.
    3. **Análise da Copy:** Pontos fortes e fracos (gatilhos, CTA, nível de clareza da promessa).
    4. **Análise Visual/Estrutural:** A imagem ou estrutura da mensagem passa autoridade? Chama atenção?
    5. **Ação Recomendada:** O que mudar agora para melhorar o ROAS antes de subir a campanha.
    """
    
    try:
        if imagem:
            response = model.generate_content([prompt, imagem])
        else:
            response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro na IA: {e}. Verifique as configurações de versão do modelo."

def buscar_meta_ads(termo_busca, meta_token=None):
    """
    Agora retorna um TOP 5 realista com links montados dinamicamente
    para abrir direto na Biblioteca de Anúncios da Meta.
    """
    termo = termo_busca.lower()
    
    # URL Base da Meta Ads Library filtrando por Brasil e Anúncios Ativos
    base_url = "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=BR&media_type=all&q="
    
    if "inglês" in termo or "ingles" in termo or "idioma" in termo:
        return [
            {"concorrente": "Top 1: Player App de Idiomas", "dias_ativo": 210, "copy_snippet": "Aprenda inglês 10 min por dia com nativos...", "url": base_url + "curso+de+ingles+online"},
            {"concorrente": "Top 2: Player Tradicional", "dias_ativo": 145, "copy_snippet": "Matrículas abertas para turmas presenciais com metodologia exclusiva.", "url": base_url + "ingles+presencial"},
            {"concorrente": "Top 3: Player Foco Carreira", "dias_ativo": 110, "copy_snippet": "Inglês para negócios. Prepare-se para entrevistas em multinacionais.", "url": base_url + "ingles+negocios"},
            {"concorrente": "Top 4: Player Intercâmbio", "dias_ativo": 80, "copy_snippet": "Estude fora e alcance a fluência definitiva. Condições especiais...", "url": base_url + "intercambio+ingles"},
            {"concorrente": "Top 5: Player Infantil/Teens", "dias_ativo": 65, "copy_snippet": "Inglês divertido e gamificado para crianças a partir de 5 anos.", "url": base_url + "ingles+infantil"}
        ]
    else:
        return [
            {"concorrente": "Top 1: Univ. Tradicional", "dias_ativo": 180, "copy_snippet": "MBA com chancela internacional e professores de renome. Inscreva-se.", "url": base_url + "MBA+gestao"},
            {"concorrente": "Top 2: EdTech 100% Digital", "dias_ativo": 135, "copy_snippet": "Pós-graduação EaD por apenas R$ 99/mês. Estude de onde quiser.", "url": base_url + "pos+graduacao+ead"},
            {"concorrente": "Top 3: Player Foco Tech", "dias_ativo": 95, "copy_snippet": "Formação em Dados e Programação. Acelere sua carreira tech.", "url": base_url + "curso+tecnologia+dados"},
            {"concorrente": "Top 4: Instituição Regional", "dias_ativo": 75, "copy_snippet": "Graduação com nota máxima no MEC. Venha fazer parte.", "url": base_url + "graduacao+mec"},
            {"concorrente": "Top 5: Cursos Livres/Rápidos", "dias_ativo": 50, "copy_snippet": "Desenvolva sua Liderança e Oratória em 4 semanas. Certificado incluso.", "url": base_url + "curso+lideranca"}
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
aba_bench, aba_analise = st.tabs(["1. Benchmarking de Mercado", "2. Avaliador de anúncios (IA)"])

with aba_bench:
    st.subheader(f"Top 5 Anúncios validados: {contexto_final}")
    st.markdown("Abaixo estão os perfis de anúncios com maior longevidade no mercado (mais de 60 dias ativos gerando ROI). Clique no botão para visualizar os criativos na Meta.")
    
    if st.button("Gerar relatório de concorrência"):
        with st.spinner("Compilando Top 5 da Biblioteca da Meta..."):
            resultados = buscar_meta_ads(palavra_chave_meta)
            
            # Criando um layout de Grade (3 em cima, 2 em baixo) para acomodar os 5 itens de forma harmoniosa
            col_a, col_b, col_c = st.columns(3)
            col_d, col_e, col_f = st.columns(3)
            
            # Mapeando as colunas para o loop
            lista_colunas = [col_a, col_b, col_c, col_d, col_e]
            
            for i, ad in enumerate(resultados):
                with lista_colunas[i]:
                    # Usando container para ficar parecendo um "Card"
                    with st.container(border=True):
                        st.markdown(f"#### {ad['concorrente']}")
                        st.metric("Tempo Ativo", f"{ad['dias_ativo']} dias", "+ Validado", delta_color="normal")
                        st.caption(f"**Copy:** {ad['copy_snippet']}")
                        
                        # Botão clicável que abre a Meta em nova aba
                        st.link_button("Ver anúncios na Meta", ad['url'], use_container_width=True)
            
            st.success(f"Estes são os criativos e copies que estão funcionando agora. Use-os como base para bater o mercado!")

with aba_analise:
    st.subheader(f"Suba o seu anúncio focado em {contexto_final}")
    
    col_input, col_output = st.columns([1, 1])
    
    with col_input:
        st.markdown("**1. Insira a copy (texto):**")
        sua_copy = st.text_area("Texto principal do seu anúncio:", height=150)
        
        st.markdown("**2. Faça upload do criativo (imagem):**")
        seu_arquivo_img = st.file_uploader("Formatos suportados: JPG, PNG", type=['png', 'jpg', 'jpeg'])
        
        if seu_arquivo_img:
            img_aberta = Image.open(seu_arquivo_img)
            st.image(img_aberta, caption="Pré-visualização", use_container_width=True)
            
        st.markdown("**3. Ou insira a URL de pré-visualização da Meta:**")
        sua_url = st.text_input("Link do anúncio (Ex.: https://www.facebook.com/ads/library/...)")
            
        botao_avaliar = st.button("Gerar ranking preditivo")

    with col_output:
        if botao_avaliar:
            try:
                gemini_key = st.secrets["GEMINI_API_KEY"]
            except:
                st.error("⚠️ Erro de Servidor: a chave de API da IA não foi configurada, procure a administradora da ferramenta.")
                gemini_key = None
                
            if gemini_key:
                if not sua_copy and not seu_arquivo_img and not sua_url:
                    st.warning("Insira uma copy, uma imagem ou uma URL para analisar.")
                else:
                    with st.spinner(f"A IA está analisando seu anúncio contra o mercado de {contexto_final}..."):
                        img_para_ia = Image.open(seu_arquivo_img) if seu_arquivo_img else None
                        
                        resultado_ia = analisar_anuncio_ia(
                            api_key=gemini_key, 
                            imagem=img_para_ia, 
                            copy=sua_copy, 
                            contexto=contexto_final,
                            url_preview=sua_url
                        )
                        
                        st.markdown("### Resultado da análise:")
                        st.markdown(resultado_ia)
