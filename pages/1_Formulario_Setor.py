import streamlit as st
from utils.auth import verificar_permissao, usuario_logado
from utils.db_queries import (
    listar_paradas, inserir_ocorrencias,
    listar_ocorrencias_por_parada, listar_usuarios
)
from utils.notifications import notificar_pmo_envio_formulario

STYLE = """
<style>
    .page-header { background:linear-gradient(135deg,#1B3A6B,#2D5AA0);color:white;
                   padding:1.5rem 2rem;border-radius:10px;margin-bottom:2rem;
                   border-left:5px solid #E87722; }
    section[data-testid="stSidebar"] { background-color:#1B3A6B !important; }
    section[data-testid="stSidebar"] * { color:white !important; }
</style>
"""

st.set_page_config(page_title="Formulário do Setor", page_icon="📋", layout="wide")
st.markdown(STYLE, unsafe_allow_html=True)
verificar_permissao(["setor","pmo","admin"])

usuario = usuario_logado()

with st.sidebar:
    st.markdown("### 📋 Formulário do Setor")
    st.markdown("---")
    paradas = listar_paradas(status="coleta")
    if not paradas:
        st.warning("Nenhuma parada em fase de coleta.")
        st.stop()
    opcoes_parada = {p["nome"]: p for p in paradas}
    parada = opcoes_parada[st.selectbox("🏗️ Parada Ativa", list(opcoes_parada.keys()))]
    parada_id = parada["id"]

st.markdown("""
<div class="page-header">
  <h1 style="margin:0;">📋 Formulário de Lições Aprendidas</h1>
  <p style="margin:5px 0 0;opacity:0.9;">Registre as ocorrências da sua área para análise do PMO</p>
</div>
""", unsafe_allow_html=True)

contrato = parada.get("contratos") or {}
c1, c2, c3 = st.columns(3)
c1.text_input("📄 Contrato",    value=f"{contrato.get('codigo','')} — {contrato.get('nome','')}", disabled=True)
c2.text_input("👤 Responsável", value=parada.get("responsavel",""), disabled=True)
c3.text_input("📅 Período",     value=f"{parada.get('data_inicio','')} → {parada.get('data_fim','')}", disabled=True)

st.markdown("---")

chave_rascunho = f"ocorrencias_{parada_id}"
chave_enviado  = f"enviado_{parada_id}"

if st.session_state.get(chave_enviado):
    st.success("✅ Formulário já enviado ao PMO. Edição bloqueada.")
    occs = listar_ocorrencias_por_parada(parada_id)
    if occs:
        import pandas as pd
        df = pd.DataFrame(occs)[["area_setor","fase","ocorrencia","impacto","licao_aprendida"]]
        df.columns = ["Área/Setor","Fase","Ocorrência","Impacto","Lição Aprendida"]
        st.dataframe(df, use_container_width=True)
    st.stop()

if chave_rascunho not in st.session_state:
    st.session_state[chave_rascunho] = [
        {"area_setor":"","fase":"","ocorrencia":"","impacto":"","licao_aprendida":""}
    ]

FASES = ["Planejamento","Mobilização","Desmontagem","Manutenção",
         "Montagem","Comissionamento","Desmobilização","Encerramento"]

linhas: list = st.session_state[chave_rascunho]
st.markdown("### 📝 Ocorrências")

indices_remover = []
for i, linha in enumerate(linhas):
    st.markdown(f"**Ocorrência #{i+1}**")
    c1, c2, c3, c4, c5, c_del = st.columns([2,2,3,3,3,0.5])
    with c1:
        linha["area_setor"] = st.text_input("Área/Setor", value=linha["area_setor"],
                                             key=f"setor_{i}", placeholder="Ex: Caldeiraria")
    with c2:
        linha["fase"] = st.selectbox("Fase", FASES,
                                     index=FASES.index(linha["fase"]) if linha["fase"] in FASES else 0,
                                     key=f"fase_{i}")
    with c3:
        linha["ocorrencia"] = st.text_area("Ocorrência", value=linha["ocorrencia"],
                                            key=f"ocor_{i}", height=100)
    with c4:
        linha["impacto"] = st.text_area("Impacto", value=linha["impacto"],
                                         key=f"imp_{i}", height=100)
    with c5:
        linha["licao_aprendida"] = st.text_area("Lição Aprendida", value=linha["licao_aprendida"],
                                                  key=f"licao_{i}", height=100)
    with c_del:
        st.markdown("<br>", unsafe_allow_html=True)
        if len(linhas) > 1 and st.button("🗑️", key=f"del_{i}"):
            indices_remover.append(i)
    st.divider()

if indices_remover:
    st.session_state[chave_rascunho] = [l for idx, l in enumerate(linhas) if idx not in indices_remover]
    st.rerun()

col_add, _ = st.columns([2,8])
with col_add:
    if st.button("➕ Adicionar Ocorrência", use_container_width=True):
        st.session_state[chave_rascunho].append(
            {"area_setor":"","fase":"","ocorrencia":"","impacto":"","licao_aprendida":""}
        )
        st.rerun()

st.markdown("---")
col_salvar, col_enviar, _ = st.columns([2,2,6])

with col_salvar:
    if st.button("💾 Salvar Rascunho", use_container_width=True):
        st.success("Rascunho salvo localmente.")

with col_enviar:
    if st.button("✅ Enviar para PMO", use_container_width=True, type="primary"):
        linhas_atuais = st.session_state[chave_rascunho]
        erros = []
        for i, l in enumerate(linhas_atuais):
            if not l["area_setor"].strip():    erros.append(f"Linha {i+1}: Área/Setor em branco.")
            if not l["ocorrencia"].strip():    erros.append(f"Linha {i+1}: Ocorrência em branco.")
            if not l["impacto"].strip():       erros.append(f"Linha {i+1}: Impacto em branco.")
            if not l["licao_aprendida"].strip():erros.append(f"Linha {i+1}: Lição Aprendida em branco.")
        if erros:
            for e in erros: st.error(e)
        else:
            payload = [
                {
                    "parada_id":       parada_id,
                    "area_setor":      l["area_setor"].strip(),
                    "fase":            l["fase"],
                    "ocorrencia":      l["ocorrencia"].strip(),
                    "impacto":         l["impacto"].strip(),
                    "licao_aprendida": l["licao_aprendida"].strip(),
                    "enviado_por":     usuario["id"],
                }
                for l in linhas_atuais
            ]
            with st.spinner("Enviando..."):
                inserir_ocorrencias(payload)
                usuarios_pmo = listar_usuarios(perfil=["pmo","admin"])
                for u in usuarios_pmo:
                    notificar_pmo_envio_formulario(
                        email_pmo       = u["email"],
                        nome_pmo        = u["nome"],
                        setor           = usuario.get("setor","Setor"),
                        parada          = parada["nome"],
                        qtd_ocorrencias = len(payload),
                    )
                st.session_state[chave_enviado] = True
            st.success(f"✅ {len(payload)} ocorrência(s) enviada(s) ao PMO!")
            st.rerun()
