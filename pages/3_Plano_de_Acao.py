import streamlit as st
from datetime import date, timedelta
from utils.auth import verificar_permissao, usuario_logado
from utils.db_queries import (
    listar_paradas, listar_ocorrencias_por_parada, listar_acoes_por_ocorrencia,
    criar_acao, deletar_acao, atualizar_status_parada, listar_usuarios, get_ocorrencia
)
from utils.gut_calculator import calcular_gut
from utils.notifications import notificar_responsavel_acao, notificar_avanco_fase

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

st.set_page_config(page_title="Plano de Ação", page_icon="📝", layout="wide")
st.markdown(STYLE, unsafe_allow_html=True)
verificar_permissao(["pmo","admin"])

usuario = usuario_logado()

with st.sidebar:
    st.markdown("### 📝 Plano de Ação")
    st.markdown("---")
    paradas = listar_paradas(status="plano_acao")
    if not paradas:
        st.warning("Nenhuma parada em fase de Plano de Ação.")
        st.stop()
    opcoes = {p["nome"]: p for p in paradas}
    parada = opcoes[st.selectbox("🏗️ Selecione a Parada", list(opcoes.keys()))]
    parada_id = parada["id"]

st.markdown("""
<div class="page-header">
  <h1 style="margin:0;">📝 Plano de Ação</h1>
  <p style="margin:5px 0 0;opacity:0.9;">Crie ações corretivas ordenadas por prioridade GUT</p>
</div>
""", unsafe_allow_html=True)

ocorrencias = listar_ocorrencias_por_parada(parada_id)
ocorrencias_ordenadas = sorted(
    ocorrencias,
    key=lambda o: (o.get("gravidade") or 0) * (o.get("urgencia") or 0) * (o.get("tendencia") or 0),
    reverse=True
)

todos_usuarios = listar_usuarios()
opcoes_usuarios = {f"{u['nome']} ({u['email']})": u for u in todos_usuarios}

if not ocorrencias_ordenadas:
    st.warning("Nenhuma ocorrência encontrada para esta parada.")
    st.stop()

st.markdown(f"**{len(ocorrencias_ordenadas)} ocorrência(s) — ordenadas por prioridade GUT**")
st.markdown("---")

for occ in ocorrencias_ordenadas:
    oid     = occ["id"]
    g       = occ.get("gravidade") or 1
    u_val   = occ.get("urgencia")  or 1
    t       = occ.get("tendencia") or 1
    gut_info = calcular_gut(g, u_val, t)
    badge    = f'<span class="gut-{gut_info["nivel"]}">{gut_info["cor"]} {gut_info["label"]} — GUT {gut_info["resultado"]}</span>'

    with st.expander(
        f"[{occ['area_setor']}] {occ['ocorrencia'][:70]}{'...' if len(occ['ocorrencia'])>70 else ''}",
        expanded=False
    ):
        st.markdown(badge, unsafe_allow_html=True)
        c_d, c_a = st.columns([2,3])
        with c_d:
            st.markdown(f"**Área/Setor:** {occ['area_setor']}")
            st.markdown(f"**Fase:** {occ['fase']}")
            st.markdown(f"**Ocorrência:** {occ['ocorrencia']}")
            st.markdown(f"**Impacto:** {occ['impacto']}")
            st.markdown(f"**Lição Aprendida:** {occ['licao_aprendida']}")
        with c_a:
            st.markdown("**Criar Nova Ação**")
            descricao = st.text_area("📌 Descrição da Ação", key=f"desc_{oid}", height=100)
            prazo     = st.date_input("📅 Prazo", value=date.today()+timedelta(days=30),
                                       key=f"prazo_{oid}", min_value=date.today())
            resp_sel  = st.selectbox("👤 Responsável", list(opcoes_usuarios.keys()), key=f"resp_{oid}")

            if st.button("➕ Adicionar Ação", key=f"add_{oid}", use_container_width=True):
                if not descricao.strip():
                    st.error("Descrição é obrigatória.")
                else:
                    resp_user = opcoes_usuarios[resp_sel]
                    criar_acao({
                        "ocorrencia_id":    oid,
                        "parada_id":        parada_id,
                        "descricao":        descricao.strip(),
                        "prazo":            str(prazo),
                        "responsavel_id":   resp_user["id"],
                        "responsavel_nome": resp_user["nome"],
                    })
                    st.success("✅ Ação criada!")
                    st.rerun()

        acoes = listar_acoes_por_ocorrencia(oid)
        if acoes:
            st.markdown("**Ações criadas:**")
            for acao in acoes:
                c1, c2, c3, c4 = st.columns([4,2,2,1])
                c1.markdown(f"📌 {acao['descricao']}")
                c2.markdown(f"📅 {acao['prazo']}")
                c3.markdown(f"👤 {acao['responsavel_nome']}")
                with c4:
                    if st.button("🗑️", key=f"del_acao_{acao['id']}"):
                        deletar_acao(acao["id"])
                        st.rerun()

st.markdown("---")
c1, _ = st.columns([3,7])
with c1:
    if st.button("🚀 Publicar Plano de Ação", use_container_width=True, type="primary"):
        with st.spinner("Publicando e notificando responsáveis..."):
            atualizar_status_parada(parada_id, "monitoramento")
            emails_notificados = set()
            for occ in ocorrencias_ordenadas:
                acoes = listar_acoes_por_ocorrencia(occ["id"])
                for acao in acoes:
                    resp = next((u for u in todos_usuarios if u["id"] == acao.get("responsavel_id")), None)
                    if resp and resp["email"] not in emails_notificados:
                        notificar_responsavel_acao(
                            email      = resp["email"],
                            nome       = resp["nome"],
                            acao       = acao["descricao"],
                            prazo      = acao["prazo"],
                            projeto    = parada["nome"],
                            ocorrencia = occ.get("ocorrencia",""),
                            nivel_gut  = occ.get("classificacao","baixo"),
                        )
                        emails_notificados.add(resp["email"])
            todos_emails = [u["email"] for u in todos_usuarios]
            notificar_avanco_fase(
                emails           = todos_emails,
                parada           = parada["nome"],
                fase_anterior    = "plano_acao",
                nova_fase        = "monitoramento",
                responsavel_acao = usuario["nome"],
            )
        st.success(f"✅ Plano publicado! {len(emails_notificados)} responsável(is) notificado(s).")
        st.balloons()
