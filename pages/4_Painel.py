import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from utils.auth import verificar_permissao, usuario_logado, get_perfil_atual
from utils.db_queries import listar_acoes, listar_paradas, listar_usuarios, atualizar_acao
from utils.notifications import notificar_atualizacao_status

STYLE = """
<style>
    .page-header { background:linear-gradient(135deg,#1B3A6B,#2D5AA0);color:white;
                   padding:1.5rem 2rem;border-radius:10px;margin-bottom:2rem;
                   border-left:5px solid #E87722; }
    .metric-card { background:white;border-radius:10px;padding:1.5rem;
                   border-top:4px solid #E87722;
                   box-shadow:0 2px 8px rgba(0,0,0,0.08);text-align:center; }
    section[data-testid="stSidebar"] { background-color:#1B3A6B !important; }
    section[data-testid="stSidebar"] * { color:white !important; }
</style>
"""

st.set_page_config(page_title="Painel", page_icon="📊", layout="wide")
st.markdown(STYLE, unsafe_allow_html=True)
verificar_permissao(["admin","pmo","setor","gestor"])

usuario = usuario_logado()
perfil  = get_perfil_atual()

st.markdown("""
<div class="page-header">
  <h1 style="margin:0;">📊 Painel de Acompanhamento</h1>
  <p style="margin:5px 0 0;opacity:0.9;">Monitore o andamento de todas as ações em tempo real</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🔍 Filtros")
    st.markdown("---")
    todas_paradas  = listar_paradas()
    todos_usuarios = listar_usuarios()
    opcoes_paradas = {p["nome"]: p["id"] for p in todas_paradas}
    opcoes_users   = {u["nome"]: u["id"] for u in todos_usuarios}

    sel_paradas  = st.multiselect("🏗️ Projeto/Parada", list(opcoes_paradas.keys()))
    sel_usuarios = st.multiselect("👤 Responsável",    list(opcoes_users.keys()))
    sel_status   = st.multiselect("📌 Status",
                                   ["pendente","em_andamento","concluido","cancelado"],
                                   format_func=lambda x: {"pendente":"Pendente",
                                                           "em_andamento":"Em Andamento",
                                                           "concluido":"Concluído",
                                                           "cancelado":"Cancelado"}[x])
    sel_gut = st.multiselect("⚡ Nível GUT", ["alto","medio","baixo"],
                              format_func=lambda x: {"alto":"🔴 Alto","medio":"🟡 Médio","baixo":"🟢 Baixo"}[x])
    hoje = date.today()
    d1 = st.date_input("De",  value=hoje - timedelta(days=180))
    d2 = st.date_input("Até", value=hoje + timedelta(days=180))

filtros = {}
if sel_paradas:  filtros["parada_ids"]      = [opcoes_paradas[n] for n in sel_paradas]
if sel_usuarios: filtros["responsavel_ids"] = [opcoes_users[n]   for n in sel_usuarios]
if sel_status:   filtros["status"]          = sel_status
if sel_gut:      filtros["gut_niveis"]      = sel_gut
if d1:           filtros["prazo_inicio"]    = d1
if d2:           filtros["prazo_fim"]       = d2

acoes_raw = listar_acoes(filtros)

rows = []
for a in acoes_raw:
    occ  = a.get("ocorrencias") or {}
    para = a.get("paradas")     or {}
    rows.append({
        "id":             a["id"],
        "Projeto":        para.get("nome",""),
        "Área/Setor":     occ.get("area_setor",""),
        "Ocorrência":     (occ.get("ocorrencia") or "")[:60],
        "GUT_nivel":      occ.get("classificacao",""),
        "Ação":           a["descricao"],
        "Responsável":    a["responsavel_nome"],
        "Prazo":          a["prazo"],
        "Status":         a["status"],
        "Comentários":    a.get("comentarios",""),
        "Data Conclusão": a.get("data_conclusao",""),
    })

df = pd.DataFrame(rows)
if df.empty:
    st.info("Nenhuma ação encontrada com os filtros aplicados.")
    st.stop()

df["Prazo"]          = pd.to_datetime(df["Prazo"]).dt.date
df["dias_restantes"] = df["Prazo"].apply(lambda p: (p - date.today()).days)
df["vencida"]        = (df["dias_restantes"] < 0)  & (df["Status"].isin(["pendente","em_andamento"]))
df["vence_em_breve"] = (df["dias_restantes"] >= 0) & (df["dias_restantes"] <= 3) & (df["Status"].isin(["pendente","em_andamento"]))

total        = len(df)
pendentes    = len(df[df["Status"] == "pendente"])
em_andamento = len(df[df["Status"] == "em_andamento"])
concluidas   = len(df[df["Status"] == "concluido"])
vencidas     = len(df[df["vencida"]])

c1, c2, c3, c4, c5 = st.columns(5)
for col, label, valor, cor in [
    (c1,"Total de Ações",  total,        "#1B3A6B"),
    (c2,"Pendentes",       pendentes,    "#1565C0"),
    (c3,"Em Andamento",    em_andamento, "#E65100"),
    (c4,"Concluídas",      concluidas,   "#2E7D32"),
    (c5,"Vencidas",        vencidas,     "#DC3545"),
]:
    col.markdown(f"""
    <div class="metric-card">
      <div style="font-size:2rem;font-weight:bold;color:{cor};">{valor}</div>
      <div style="color:#666;font-size:14px;">{label}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

STATUS_MAP = {"pendente":"Pendente","em_andamento":"Em Andamento",
              "concluido":"Concluído","cancelado":"Cancelado"}

cg1, cg2 = st.columns(2)
with cg1:
    df_s = df["Status"].value_counts().reset_index()
    df_s.columns = ["Status","Qtd"]
    df_s["Status"] = df_s["Status"].map(STATUS_MAP).fillna(df_s["Status"])
    fig = px.pie(df_s, names="Status", values="Qtd", title="Distribuição por Status",
                 color_discrete_sequence=["#1565C0","#E65100","#2E7D32","#616161"])
    st.plotly_chart(fig, use_container_width=True)

with cg2:
    df_p = df["Projeto"].value_counts().reset_index()
    df_p.columns = ["Projeto","Ações"]
    fig = px.bar(df_p, x="Projeto", y="Ações", title="Ações por Projeto",
                 color_discrete_sequence=["#1B3A6B"])
    st.plotly_chart(fig, use_container_width=True)

cg3, cg4 = st.columns(2)
with cg3:
    df_r = df["Responsável"].value_counts().reset_index()
    df_r.columns = ["Responsável","Ações"]
    fig = px.bar(df_r, x="Ações", y="Responsável", orientation="h",
                 title="Ações por Responsável", color_discrete_sequence=["#E87722"])
    st.plotly_chart(fig, use_container_width=True)

with cg4:
    df_c = df[df["Status"] == "concluido"].copy()
    if not df_c.empty:
        df_c["Data Conclusão"] = pd.to_datetime(df_c["Data Conclusão"], errors="coerce")
        df_c = df_c.dropna(subset=["Data Conclusão"]).sort_values("Data Conclusão")
        df_c["Acumulado"] = range(1, len(df_c)+1)
        fig = px.line(df_c, x="Data Conclusão", y="Acumulado",
                      title="Conclusões ao Longo do Tempo",
                      color_discrete_sequence=["#28A745"])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma ação concluída ainda.")

st.markdown("---")
st.markdown("### 📋 Tabela de Ações")

GUT_BADGE    = {"alto":"🔴 Alto","medio":"🟡 Médio","baixo":"🟢 Baixo","":  "—", None: "—"}
STATUS_LABEL = {"pendente":"🔵 Pendente","em_andamento":"🟠 Em Andamento",
                "concluido":"🟢 Concluído","cancelado":"⚫ Cancelado"}

def highlight_row(row):
    if row["vencida"]:        return ["background-color:#FFEAEA"] * len(row)
    elif row["vence_em_breve"]:return ["background-color:#FFF8E1"] * len(row)
    return [""] * len(row)

df_exib = df.copy()
df_exib["GUT"]           = df_exib["GUT_nivel"].map(GUT_BADGE).fillna("—")
df_exib["Dias Restantes"]= df_exib["dias_restantes"].apply(lambda d: f"{'⚠️ ' if d<0 else ''}{d}d")
df_exib["Status_label"]  = df_exib["Status"].map(STATUS_LABEL).fillna(df_exib["Status"])

colunas = ["Projeto","Área/Setor","Ocorrência","GUT","Ação","Responsável",
           "Prazo","Dias Restantes","Status_label","vencida","vence_em_breve"]
df_styled = df_exib[colunas].style.apply(highlight_row, axis=1)
st.dataframe(df_styled, use_container_width=True, hide_index=True,
             column_config={"vencida": None, "vence_em_breve": None,
                            "Status_label": st.column_config.TextColumn("Status")})

st.markdown("---")
st.markdown("### ✏️ Atualizar Status de Ação")

if perfil == "gestor":
    st.info("👁️ Perfil Gestor: acesso somente leitura.")
else:
    opcoes_acoes = {
        f"{r['Ação'][:60]} — {r['Responsável']}": r["id"]
        for _, r in df_exib.iterrows()
    }
    acao_sel_label = st.selectbox("Selecione a ação", list(opcoes_acoes.keys()))
    acao_id_sel    = opcoes_acoes[acao_sel_label]
    acao_atual     = df[df["id"] == acao_id_sel].iloc[0]

    with st.form("form_atualizar"):
        cs, cc = st.columns([2,4])
        novo_status = cs.selectbox(
            "Novo Status",
            ["pendente","em_andamento","concluido","cancelado"],
            index=["pendente","em_andamento","concluido","cancelado"].index(acao_atual["Status"]),
            format_func=lambda x: STATUS_LABEL.get(x, x),
        )
        comentario  = cc.text_area("Comentário (opcional)")
        submitted   = st.form_submit_button("💾 Salvar Atualização", type="primary")

    if submitted:
        atualizar_acao(acao_id_sel, novo_status, comentario.strip() or None)
        usuarios_pmo = listar_usuarios(perfil=["pmo","admin"])
        for u in usuarios_pmo:
            notificar_atualizacao_status(
                email_pmo        = u["email"],
                nome_pmo         = u["nome"],
                responsavel_nome = usuario["nome"],
                acao             = acao_atual["Ação"],
                status_anterior  = acao_atual["Status"],
                novo_status      = novo_status,
                comentario       = comentario.strip(),
                projeto          = acao_atual["Projeto"],
            )
        st.success("✅ Status atualizado e PMO notificado!")
        st.rerun()
