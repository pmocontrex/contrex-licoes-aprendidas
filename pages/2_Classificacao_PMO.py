import streamlit as st
from utils.auth import verificar_permissao, usuario_logado
from utils.db_queries import (
    listar_paradas, listar_ocorrencias_por_parada,
    classificar_ocorrencia, atualizar_status_parada, listar_usuarios
)
from utils.gut_calculator import calcular_gut, get_descricao_gravidade, get_descricao_urgencia, get_descricao_tendencia
from utils.notifications import notificar_avanco_fase

STYLE = """
<style>
    .page-header { background:linear-gradient(135deg,#1B3A6B,#2D5AA0);color:white;
                   padding:1.5rem 2rem;border-radius:10px;margin-bottom:2rem;
                   border-left:5px solid #E87722; }
    .gut-alto  { background:#FFEAEA;color:#DC3545;padding:3px 10px;border-radius:20px;
                 font-weight:bold;display:inline-block; }
    .gut-medio { background:#FFF8E1;color:#856404;padding:3px 10px;border-radius:20px;
                 font-weight:bold;display:inline-block; }
    .gut-baixo { background:#E8F5E9;color:#28A745;padding:3px 10px;border-radius:20px;
                 font-weight:bold;display:inline-block; }
    section[data-testid="stSidebar"] { background-color:#1B3A6B !important; }
    section[data-testid="stSidebar"] * { color:white !important; }
</style>
"""

st.set_page_config(page_title="Classificação GUT", page_icon="🔬", layout="wide")
st.markdown(STYLE, unsafe_allow_html=True)
verificar_permissao(["pmo","admin"])

usuario = usuario_logado()

with st.sidebar:
    st.markdown("### 🔬 Classificação GUT")
    st.markdown("---")
    paradas = listar_paradas(status=["coleta","classificacao"])
    if not paradas:
        st.warning("Nenhuma parada disponível para classificação.")
        st.stop()
    opcoes = {p["nome"]: p for p in paradas}
    parada = opcoes[st.selectbox("🏗️ Selecione a Parada", list(opcoes.keys()))]
    parada_id = parada["id"]

st.markdown("""
<div class="page-header">
  <h1 style="margin:0;">🔬 Classificação GUT</h1>
  <p style="margin:5px 0 0;opacity:0.9;">Classifique cada ocorrência com a Matriz GUT para priorização</p>
</div>
""", unsafe_allow_html=True)

with st.expander("ℹ️ Guia de Classificação GUT", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Gravidade (G)**")
        for n in range(1,6): st.markdown(f"**{n}** — {get_descricao_gravidade(n)}")
    with c2:
        st.markdown("**Urgência (U)**")
        for n in range(1,6): st.markdown(f"**{n}** — {get_descricao_urgencia(n)}")
    with c3:
        st.markdown("**Tendência (T)**")
        for n in range(1,6): st.markdown(f"**{n}** — {get_descricao_tendencia(n)}")
    st.info("**GUT = G × U × T** | 🟢 1–25 Baixo | 🟡 26–74 Médio | 🔴 75–125 Alto")

ocorrencias = listar_ocorrencias_por_parada(parada_id)
if not ocorrencias:
    st.warning("Esta parada não possui ocorrências registradas.")
    st.stop()

st.markdown(f"**{len(ocorrencias)} ocorrência(s) para classificar**")
st.markdown("---")

chave_gut = f"gut_{parada_id}"
if chave_gut not in st.session_state:
    st.session_state[chave_gut] = {}

for occ in ocorrencias:
    oid = occ["id"]
    if oid not in st.session_state[chave_gut]:
        st.session_state[chave_gut][oid] = {
            "g": occ.get("gravidade") or 1,
            "u": occ.get("urgencia") or 1,
            "t": occ.get("tendencia") or 1,
        }
    vals = st.session_state[chave_gut][oid]

    with st.expander(
        f"📌 [{occ['area_setor']}] {occ['ocorrencia'][:80]}{'...' if len(occ['ocorrencia'])>80 else ''}",
        expanded=(occ.get("classificacao") is None)
    ):
        c_info, c_gut = st.columns([3,2])
        with c_info:
            st.markdown(f"**Área/Setor:** {occ['area_setor']}")
            st.markdown(f"**Fase:** {occ['fase']}")
            st.markdown(f"**Ocorrência:** {occ['ocorrencia']}")
            st.markdown(f"**Impacto:** {occ['impacto']}")
            st.markdown(f"**Lição Aprendida:** {occ['licao_aprendida']}")
        with c_gut:
            st.markdown("#### Classificação GUT")
            g = st.selectbox("Gravidade", list(range(1,6)), index=vals["g"]-1, key=f"g_{oid}",
                             help="\n".join([f"{n}: {get_descricao_gravidade(n)}" for n in range(1,6)]))
            u = st.selectbox("Urgência",  list(range(1,6)), index=vals["u"]-1, key=f"u_{oid}",
                             help="\n".join([f"{n}: {get_descricao_urgencia(n)}" for n in range(1,6)]))
            t = st.selectbox("Tendência", list(range(1,6)), index=vals["t"]-1, key=f"t_{oid}",
                             help="\n".join([f"{n}: {get_descricao_tendencia(n)}" for n in range(1,6)]))
            st.session_state[chave_gut][oid] = {"g": g, "u": u, "t": t}
            r = calcular_gut(g, u, t)
            st.markdown(f"**Resultado:** {r['cor']} **{r['resultado']}** — {r['label']}")

st.markdown("---")
c1, c2, _ = st.columns([2,2,6])

with c1:
    if st.button("💾 Salvar Classificações", use_container_width=True, type="primary"):
        with st.spinner("Salvando..."):
            for oid, vals in st.session_state[chave_gut].items():
                classificar_ocorrencia(oid, vals["g"], vals["u"], vals["t"])
        st.success("✅ Classificações salvas!")

with c2:
    if st.button("▶️ Avançar para Plano de Ação", use_container_width=True):
        with st.spinner("Salvando e avançando..."):
            for oid, vals in st.session_state[chave_gut].items():
                classificar_ocorrencia(oid, vals["g"], vals["u"], vals["t"])
            atualizar_status_parada(parada_id, "plano_acao")
            todos_emails = [u["email"] for u in listar_usuarios()]
            notificar_avanco_fase(
                emails           = todos_emails,
                parada           = parada["nome"],
                fase_anterior    = parada["status"],
                nova_fase        = "plano_acao",
                responsavel_acao = usuario["nome"],
            )
        st.success("✅ Parada avançada para Plano de Ação! Equipe notificada.")
        st.balloons()
