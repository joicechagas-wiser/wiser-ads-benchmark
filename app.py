import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
from datetime import datetime

# Configurações da página e identidade visual
st.set_page_config(page_title="Wiser Ads Benchmark", page_icon="🪽", layout="wide")

st.markdown("""
    <style>
    h1, h2, h3 { color: #621E4F !important; }
    .stButton>button { background-color: #204364; color: white; border-radius: 8px; }
    .stButton>button:hover { background-color: #621E4F; color: white; border-color: #621E4F; }
    </style>
    """, unsafe_allow_html=True)

# Inicia a memória do aplicativo para guardar o Top 5 da concorrência
if 'top5_concorrentes' not in st.session_state:
    st.session_state['top5_concorrentes'] = []

# Funções de back-end e IA
def analisar_anuncio_ia(api_key, imagem, copy, contexto, url_preview="", concorrentes_base=[]):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    
    # Prepara o texto dos concorrentes para a IA ler
    texto_concorrencia = ""
    if concorrentes_base:
        texto_concorrencia = "\n\n### PADRÃO OURO DO MERCADO (USE COMO BENCHMARK):\n"
        for ad in concorrentes_base:
            texto_concorrencia += f"- Concorrente rodando há {ad['dias_ativo']} dias. Copy: '{ad['copy_snippet']}'\n"
    
    prompt = f"""
    Você é um especialista em Growth Marketing e Mídia Paga no nicho de Educação.
    Estou te enviando as informações de um NOVO anúncio que criamos.
    
    Copy do Meu Anúncio: "{copy}"
    Contexto do Nicho e Modalidade: "{contexto}"
    URL de Pré-visualização da Meta (Meu anúncio): "{url_preview}"
    {texto_concorrencia}
    
    Sua missão é avaliar o meu anúncio frente ao mercado. SE eu tiver te passado o "Padrão Ouro do Mercado" acima, use ele como régua de comparação estrita. Compare meus gatilhos e promessas com os deles.
    
    Me retorne UMA ANÁLISE ESTRUTURADA EM MARKDOWN com:
    1. **EduScore (0 a 100):** Uma nota geral para o potencial de conversão do meu criativo comparado ao mercado.
    2. **Estimativa Competitiva:** Estimativa se meu CPL e CTR ficarão Acima, Abaixo ou na Média do mercado.
    3. **Análise da Copy:** Pontos fortes e fracos frente aos concorrentes vencedores.
    4. **Análise Visual/Estrutural:** A imagem passa autoridade? Chama mais atenção que a média do mercado?
    5. **Ação Recomendada:** O que eu devo mudar agora na copy ou arte para bater a concorrência?
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
    Conecta na API REAL da Meta. Se o token não existir ou falhar, 
    usa os dados simulados (Fallback) para o app não quebrar.
    """ 
    termo = termo_busca.lower()     
    
    # Tentativa 1: conexão com a API oficial da Meta
    if meta_token and meta_token != "":
        url = "https://graph.facebook.com/v25.0/ads_archive"
        termo_exato = f'"{termo_busca}"'
        
        params = {
            "search_terms": termo_exato,
            "ad_type": "ALL",
            "ad_active_status": "ACTIVE",
            "ad_reached_countries": "['BR']",
            "fields": "id,page_name,ad_delivery_start_time,ad_creative_bodies,ad_snapshot_url",
            "access_token": meta_token,
            "limit": 200 # Puxa 200 anúncios para podermos ranquear os mais velhos
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if "data" in data and len(data["data"]) > 0:
                resultados_reais = []
                hoje = datetime.now()
                
                for ad in data["data"]:
                    # Calcula quantos dias o anúncio está rodando
                    data_inicio_str = ad.get("ad_delivery_start_time")
                    if data_inicio_str:
                        data_inicio = datetime.strptime(data_inicio_str[:10], "%Y-%m-%d")
                        dias_ativo = (hoje - data_inicio).days
                    else:
                        dias_ativo = 0
                        
                    # Pega a copy e limita a 150 caracteres para o card
                    copy_completa = ad.get("ad_creative_bodies", [""])[0] if ad.get("ad_creative_bodies") else "Anúncio focado em mídia visual (Sem texto)."
                    copy_snippet = copy_completa[:150] + "..." if len(copy_completa) > 150 else copy_completa
                    
                    resultados_reais.append({
                        "concorrente": ad.get("page_name", "Página Oculta"),
                        "dias_ativo": dias_ativo,
                        "copy_snippet": copy_snippet,
                        "url": ad.get("ad_snapshot_url", "https://www.facebook.com/ads/library/")
                    })
 
                # Ordena do mais antigo (mais validado) para o mais novo e pega o Top 5 
                resultados_reais = sorted(resultados_reais, key=lambda x: x["dias_ativo"], reverse=True)
                return resultados_reais[:5]
                
        except Exception as e:
            st.warning(f"Aviso: Falha ao processar os dados da Meta. Usando dados de backup. Erro: {e}")

    # Fallback: dados simulados (caso o token Meta não esteja configurado)
    base_url = "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=BR&media_type=all&q="
    if "inglês" in termo or "ingles" in termo or "idioma" in termo:
        return [
            {"concorrente": "Top 1: Player App de Idiomas", "dias_ativo": 210, "copy_snippet": "Aprenda inglês 10 min por dia com nativos...", "url": base_url + "curso+de+ingles+online"},
            {"concorrente": "Top 2: Player Tradicional", "dias_ativo": 145, "copy_snippet": "Matrículas abertas para turmas presenciais com metodologia exclusiva.", "url": base_url + "ingles+presencial"},
            {"concorrente": "Top 3: Player Foco Carreira", "dias_ativo": 110, "copy_snippet": "Inglês para negócios. Prepare-se para entrevistas em multinacionais.", "url": base_url + "ingles+negocios"}
        ]
    else:
        return [
            {"concorrente": "Top 1: Univ. Tradicional", "dias_ativo": 180, "copy_snippet": "MBA com chancela internacional e professores de renome. Inscreva-se.", "url": base_url + "MBA+gestao"},
            {"concorrente": "Top 2: EdTech 100% Digital", "dias_ativo": 135, "copy_snippet": "Pós-graduação EaD por apenas R$ 99/mês. Estude de onde quiser.", "url": base_url + "pos+graduacao+ead"},
            {"concorrente": "Top 3: Player Foco Tech", "dias_ativo": 95, "copy_snippet": "Formação em Dados e Programação. Acelere sua carreira tech.", "url": base_url + "curso+tecnologia+dados"}
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
        "Pós-graduação", 
        "Cursos de Inglês", 
        "Graduação", 
        "MBA", 
        "Cursos Livres (Soft/Hard Skills)"
    ])
    
    if nicho == "Cursos de Inglês":
        modalidade = st.radio("Selecione a Modalidade:", ["Online", "Presencial"])
        contexto_final = f"{nicho} ({modalidade})"
        sugestao_busca = f"Curso de Inglês {modalidade}"
    else:
        contexto_final = nicho
        sugestao_busca = nicho
        
    palavra_chave_meta = st.text_input("Termo para buscar na Meta Ads:", value=sugestao_busca)

# Chaves
try:
    gemini_key = st.secrets["GEMINI_API_KEY"]
except:
    gemini_key = None

try:
    meta_key = st.secrets["META_ACCESS_TOKEN"]
except:
    meta_key = None

# Abas principais
aba_bench, aba_analise = st.tabs(["1. Benchmarking de Mercado", "2. Avaliador de anúncios (IA)"])

with aba_bench:
    st.subheader(f"Top 5 anúncios validados: {contexto_final}")
    st.markdown("Abaixo estão os anúncios com maior longevidade no mercado. Clique no botão para visualizá-os na Meta.")
    
    if st.button("Gerar relatório de concorrência"):
        with st.spinner("Minerando dados da biblioteca da Meta..."):
            resultados = buscar_meta_ads(palavra_chave_meta, meta_key)
            
            if not resultados or "erro" in resultados:
                st.error("Nenhum anúncio encontrado ou erro na API.")
            else:
                # Salvando na memória para a aba 2 ler posteriormente
                st.session_state['top5_concorrentes'] = resultados
                
                col_a, col_b, col_c = st.columns(3)
                col_d, col_e, col_f = st.columns(3)
                lista_colunas = [col_a, col_b, col_c, col_d, col_e]
                
                for i, ad in enumerate(resultados):
                    if i < 5:
                        with lista_colunas[i]:
                            with st.container(border=True):
                                st.markdown(f"#### {ad['concorrente']}")
                                st.metric("Tempo Ativo", f"{ad['dias_ativo']} dias", "+ Validado", delta_color="normal")
                                st.caption(f"**Copy:** {ad['copy_snippet']}")
                                st.link_button("Ver anúncio na Meta", ad['url'], use_container_width=True)
                
                st.success(f"Estes são os criativos que estão funcionando agora. A IA usará este Top 5 como régua na aba 2!")

with aba_analise:
    st.subheader(f"Suba o seu novo anúncio focado em {contexto_final}")
    
    # Verifica se já temos o Top 5 salvo para avisar o usuário
    if len(st.session_state['top5_concorrentes']) > 0:
        st.info("A IA já está conectada aos concorrentes da aba 1 e fará uma análise comparativa direta!")
    else:
        st.warning("Você ainda não gerou o relatório da aba 1. A IA usará o conhecimento de mercado geral, não o Top 5 atualizado.")
    
    col_input, col_output = st.columns([1, 1])
    
    with col_input:
        st.markdown("**1. Insira a copy (texto):**")
        sua_copy = st.text_area("Texto principal do seu anúncio:", height=150)
        
        st.markdown("**2. Faça upload do criativo (imagem):**")
        seu_arquivo_img = st.file_uploader("Formatos suportados: JPG, PNG", type=['png', 'jpg', 'jpeg'])
        
        if seu_arquivo_img:
            img_aberta = Image.open(seu_arquivo_img)
            st.image(img_aberta, caption="Pré-visualização", use_container_width=True)
            
        st.markdown("**3. Ou Insira a URL de pré-visualização da Meta:**")
        sua_url = st.text_input("Link do anúncio (Ex.: https://www.facebook.com/ads/library/...)")
            
        botao_avaliar = st.button("Gerar ranking preditivo")

    with col_output:
        if botao_avaliar:
            if not gemini_key:
                st.error("⚠️ Erro de Servidor: a chave de API da IA não foi configurada, entre em contato com a administradora da ferramenta.")
            elif not sua_copy and not seu_arquivo_img and not sua_url:
                st.warning("Insira uma copy, uma imagem ou uma URL para analisar.")
            else:
                with st.spinner(f"A IA está analisando seu anúncio contra o padrão do mercado de {contexto_final}..."):
                    img_para_ia = Image.open(seu_arquivo_img) if seu_arquivo_img else None
                    
                    # Passando a memória (Top 5) para a função da IA
                    resultado_ia = analisar_anuncio_ia(
                        api_key=gemini_key, 
                        imagem=img_para_ia, 
                        copy=sua_copy, 
                        contexto=contexto_final,
                        url_preview=sua_url,
                        concorrentes_base=st.session_state['top5_concorrentes']
                    )
                    
                    st.markdown("### Resultado da análise:")
                    st.markdown(resultado_ia)
