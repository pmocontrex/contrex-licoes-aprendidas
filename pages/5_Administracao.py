import streamlit as st
from datetime import date
from utils.auth import verificar_permissao, usuario_logado
from utils.supabase_client import get_supabase, get_supabase_admin
from utils.db_queries import listar_contratos, listar_paradas, listar_usuarios
from utils.notifications import notificar_avanco_fase

STYLE = """
<style>
    .page-header { background:linear-gradient(135deg,#1B3A6B,#2D5AA0);color:white;
                   padding:1.5rem 2rem;border-radius:10px;margin-bottom:2rem;
                   border-left:5px solid #E87722; }
    section[data-testid="stSidebar"] { background-color:#1B3A6B !important; }
    section[data-testid="stSidebar"] * { color:white !important; }
</style>
"""

st.set_page_config(page_title="Administração", page_icon="⚙️", layout="wide")
st.markdown(STYLE, unsafe_allow_html=True)
verificar_permissao(["admin","pmo"])

usuario = usuario_logado()
perfil  = usuario.get("perfil")

with st.sidebar:
    st.markdown("### ⚙️ Administração")
    st.markdown("---")
    aba = st.radio("Módulo", ["👤 Usuários","📄 Contratos","🏗️ Paradas"],
                   label_visibility="collapsed")

st.markdown("""
<div class="page-header">
  <h1 style="margin:0;">⚙️ Administração do Sistema</h1>
  <p style="margin:5px 0 0;opacity:0.9;">Gerencie usuários, contratos e paradas</p>
</div>
""", unsafe_allow_html=True)

FLUXO      = ["coleta","classificacao","plano_acao","monitoramento","encerrada"]
STATUS_ICON = {"coleta":"🔵","classificacao":"🟡","plano_acao":"🟠",
               "monitoramento":"🟢","encerrada":"⚫"}
STATUS_NOME = {"coleta":"Coleta","classificacao":"Classificação GUT",
               "plano_acao":"Plano de Ação","monitoramento":"Monitoramento","encerrada":"Encerrada"}


# ================================================================
# USUÁRIOS
# ================================================================
if aba == "👤 Usuários":
    verificar_permissao(["admin"])
    st.markdown("## 👤 Gerenciamento de Usuários")
    tab_novo, tab_lista = st.tabs(["➕ Novo Usuário","📋 Usuários Cadastrados"])

    with tab_novo:
        st.markdown("### Criar Novo Usuário")
        st.info("O sistema criará o login e enviará acesso com e-mail e senha definidos aqui.")
        with st.form("form_novo_usuario", clear_on_submit=True):
            c1, c2  = st.columns(2)
            nome    = c1.text_input("👤 Nome Completo *")
            email   = c2.text_input("📧 E-mail *")
            c3, c4  = st.columns(2)
            senha   = c3.text_input("🔒 Senha Inicial *", type="password",
                                     help="Mínimo 6 caracteres")
            perfil_novo = c4.selectbox("🎭 Perfil *",
                                        ["setor","pmo","gestor","admin"],
                                        format_func=lambda x: {
                                            "setor":  "Setor — Preenche formulários",
                                            "pmo":    "PMO — Classifica e cria planos",
                                            "gestor": "Gestor — Somente leitura",
                                            "admin":  "Admin — Acesso total",
                                        }[x])
            setor_nome = st.text_input("🏭 Setor *",
                                       placeholder="Ex: Caldeiraria",
                                       help="Obrigatório apenas para perfil Setor") if perfil_novo == "setor" else ""
            submitted = st.form_submit_button("✅ Criar Usuário", type="primary", use_container_width=True)

        if submitted:
            erros = []
            if not nome.strip():  erros.append("Nome é obrigatório.")
            if not email.strip(): erros.append("E-mail é obrigatório.")
            if len(senha) < 6:    erros.append("Senha deve ter no mínimo 6 caracteres.")
            if perfil_novo == "setor" and not setor_nome.strip():
                erros.append("Setor é obrigatório para o perfil Setor.")
            if erros:
                for e in erros: st.error(e)
            else:
                with st.spinner("Criando usuário..."):
                    try:
                        sb_admin = get_supabase_admin()
                        resp     = sb_admin.auth.admin.create_user({
                            "email":         email.strip().lower(),
                            "password":      senha,
                            "email_confirm": True,
                        })
                        user_id = resp.user.id
                        get_supabase().table("perfis_usuarios").insert({
                            "id":     user_id,
                            "nome":   nome.strip(),
                            "email":  email.strip().lower(),
                            "perfil": perfil_novo,
                            "setor":  setor_nome.strip() or None,
                            "ativo":  True,
                        }).execute()
                        st.success(f"✅ Usuário **{nome}** criado! Perfil: **{perfil_novo.upper()}**")
                    except Exception as e:
                        st.error(f"❌ Erro ao criar usuário: {e}")

    with tab_lista:
        st.markdown("### Usuários Cadastrados")
        c1, c2 = st.columns(2)
        f_perfil = c1.selectbox("Filtrar por perfil", ["Todos","admin","pmo","setor","gestor"])
        f_ativo  = c2.selectbox("Filtrar por status", ["Todos","Ativo","Inativo"])

        todos = listar_usuarios()
        if f_perfil != "Todos": todos = [u for u in todos if u["perfil"] == f_perfil]
        if f_ativo == "Ativo":   todos = [u for u in todos if u["ativo"]]
        elif f_ativo == "Inativo":todos = [u for u in todos if not u["ativo"]]

        for u in todos:
            c_i, c_n, c_e, c_p, c_s, c_btn = st.columns([0.5,2,3,1.5,2,1.5])
            c_i.markdown(f"<br>{'🟢' if u['ativo'] else '🔴'}", unsafe_allow_html=True)
            c_n.markdown(f"<br>**{u['nome']}**",            unsafe_allow_html=True)
            c_e.markdown(f"<br>{u['email']}",               unsafe_allow_html=True)
            c_p.markdown(f"<br>`{u['perfil'].upper()}`",    unsafe_allow_html=True)
            c_s.markdown(f"<br>{u.get('setor') or '—'}",    unsafe_allow_html=True)
            with c_btn:
                st.markdown("<br>", unsafe_allow_html=True)
                label_btn = "🔴 Desativar" if u["ativo"] else "🟢 Ativar"
                if st.button(label_btn, key=f"toggle_{u['id']}", use_container_width=True):
                    get_supabase().table("perfis_usuarios").update(
                        {"ativo": not u["ativo"]}
                    ).eq("id", u["id"]).execute()
                    st.rerun()
            st.divider()

        st.markdown("### ✏️ Editar Usuário")
        todos_edit = listar_usuarios()
        if todos_edit:
            opcoes_edit = {f"{u['nome']} ({u['email']})": u for u in todos_edit}
            u_edit = opcoes_edit[st.selectbox("Selecione", list(opcoes_edit.keys()))]
            with st.form("form_editar_usuario"):
                c1, c2 = st.columns(2)
                novo_nome   = c1.text_input("Nome",   value=u_edit["nome"])
                novo_perfil = c2.selectbox("Perfil",  ["setor","pmo","gestor","admin"],
                                            index=["setor","pmo","gestor","admin"].index(u_edit["perfil"]))
                novo_setor  = st.text_input("Setor",  value=u_edit.get("setor") or "")
                nova_senha  = st.text_input("Nova Senha (deixe em branco para não alterar)",
                                             type="password")
                salvar = st.form_submit_button("💾 Salvar Alterações", type="primary")
            if salvar:
                with st.spinner("Salvando..."):
                    try:
                        get_supabase().table("perfis_usuarios").update({
                            "nome":   novo_nome.strip(),
                            "perfil": novo_perfil,
                            "setor":  novo_setor.strip() or None,
                        }).eq("id", u_edit["id"]).execute()
                        if nova_senha.strip():
                            if len(nova_senha) < 6:
                                st.error("Senha deve ter no mínimo 6 caracteres.")
                            else:
                                get_supabase_admin().auth.admin.update_user_by_id(
                                    u_edit["id"], {"password": nova_senha}
                                )
                        st.success("✅ Usuário atualizado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro: {e}")


# ================================================================
# CONTRATOS
# ================================================================
elif aba == "📄 Contratos":
    st.markdown("## 📄 Gerenciamento de Contratos")
    tab_novo, tab_lista = st.tabs(["➕ Novo Contrato","📋 Contratos Cadastrados"])

    with tab_novo:
        with st.form("form_novo_contrato", clear_on_submit=True):
            c1, c2      = st.columns(2)
            codigo      = c1.text_input("🔖 Código *", placeholder="Ex: CON-2025-001")
            responsavel = c2.text_input("👤 Responsável *")
            nome_c      = st.text_input("📋 Nome do Contrato *",
                                         placeholder="Ex: Refinaria Alpha — Parada Geral 2025")
            submitted   = st.form_submit_button("✅ Cadastrar", type="primary", use_container_width=True)

        if submitted:
            erros = []
            if not codigo.strip():      erros.append("Código é obrigatório.")
            if not nome_c.strip():      erros.append("Nome é obrigatório.")
            if not responsavel.strip(): erros.append("Responsável é obrigatório.")
            if erros:
                for e in erros: st.error(e)
            else:
                try:
                    get_supabase().table("contratos").insert({
                        "codigo":      codigo.strip().upper(),
                        "nome":        nome_c.strip(),
                        "responsavel": responsavel.strip(),
                    }).execute()
                    st.success(f"✅ Contrato **{codigo.upper()}** cadastrado!")
                except Exception as e:
                    if "unique" in str(e).lower():
                        st.error(f"❌ Código **{codigo.upper()}** já existe.")
                    else:
                        st.error(f"❌ Erro: {e}")

    with tab_lista:
        contratos = listar_contratos()
        if not contratos:
            st.info("Nenhum contrato cadastrado.")
        for c in contratos:
            with st.expander(f"📄 {c['codigo']} — {c['nome']}"):
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**Código:** {c['codigo']}")
                c2.markdown(f"**Responsável:** {c['responsavel']}")
                c3.markdown(f"**Cadastrado em:** {str(c['criado_em'])[:10]}")
                if perfil == "admin":
                    with st.form(f"edit_c_{c['id']}"):
                        e_nome = st.text_input("Nome",        value=c["nome"])
                        e_resp = st.text_input("Responsável", value=c["responsavel"])
                        if st.form_submit_button("💾 Salvar"):
                            get_supabase().table("contratos").update({
                                "nome": e_nome.strip(), "responsavel": e_resp.strip()
                            }).eq("id", c["id"]).execute()
                            st.success("✅ Atualizado!")
                            st.rerun()


# ================================================================
# PARADAS
# ================================================================
elif aba == "🏗️ Paradas":
    st.markdown("## 🏗️ Gerenciamento de Paradas")
    tab_novo, tab_lista = st.tabs(["➕ Nova Parada","📋 Paradas Cadastradas"])

    with tab_novo:
        contratos = listar_contratos()
        if not contratos:
            st.warning("⚠️ Cadastre um contrato antes de criar uma parada.")
            st.stop()
        with st.form("form_nova_parada", clear_on_submit=True):
            from datetime import timedelta
            opcoes_c  = {f"{c['codigo']} — {c['nome']}": c for c in contratos}
            sel_c     = st.selectbox("📄 Contrato *", list(opcoes_c.keys()))
            contrato  = opcoes_c[sel_c]
            c1, c2    = st.columns(2)
            nome_p    = c1.text_input("🏗️ Nome da Parada *", placeholder="Ex: PG-2025-Alpha")
            resp_p    = c2.text_input("👤 Responsável *", value=contrato["responsavel"])
            c3, c4    = st.columns(2)
            d_ini     = c3.date_input("📅 Início *", value=date.today())
            d_fim     = c4.date_input("📅 Fim *",    value=date.today()+timedelta(days=30))
            status_i  = st.selectbox("📌 Status Inicial",
                                      ["coleta","classificacao","plano_acao","monitoramento"],
                                      format_func=lambda x: f"{STATUS_ICON[x]} {STATUS_NOME[x]}")
            submitted = st.form_submit_button("✅ Cadastrar Parada", type="primary", use_container_width=True)

        if submitted:
            erros = []
            if not nome_p.strip(): erros.append("Nome é obrigatório.")
            if not resp_p.strip(): erros.append("Responsável é obrigatório.")
            if d_fim <= d_ini:     erros.append("Data fim deve ser posterior ao início.")
            if erros:
                for e in erros: st.error(e)
            else:
                try:
                    get_supabase().table("paradas").insert({
                        "contrato_id": contrato["id"],
                        "nome":        nome_p.strip(),
                        "responsavel": resp_p.strip(),
                        "data_inicio": str(d_ini),
                        "data_fim":    str(d_fim),
                        "status":      status_i,
                        "criado_por":  usuario["id"],
                    }).execute()
                    st.success(f"✅ Parada **{nome_p}** cadastrada!")
                except Exception as e:
                    st.error(f"❌ Erro: {e}")

    with tab_lista:
        f_status  = st.selectbox("Filtrar por status",
                                  ["Todos"] + FLUXO,
                                  format_func=lambda x: "Todos" if x == "Todos"
                                                         else f"{STATUS_ICON[x]} {STATUS_NOME[x]}")
        paradas   = listar_paradas()
        if f_status != "Todos":
            paradas = [p for p in paradas if p["status"] == f_status]

        for p in paradas:
            contrato_info = p.get("contratos") or {}
            icone = STATUS_ICON.get(p["status"],"🔵")
            with st.expander(f"{icone} {p['nome']} — {contrato_info.get('codigo','')}"):
                c1, c2, c3, c4 = st.columns(4)
                c1.markdown(f"**Contrato:** {contrato_info.get('codigo','')} — {contrato_info.get('nome','')}")
                c2.markdown(f"**Responsável:** {p['responsavel']}")
                c3.markdown(f"**Período:** {p['data_inicio']} → {p['data_fim']}")
                c4.markdown(f"**Status:** {icone} {STATUS_NOME.get(p['status'],p['status'])}")
                st.markdown("---")

                idx_atual = FLUXO.index(p["status"]) if p["status"] in FLUXO else 0
                c_prev, c_next, c_edit = st.columns([2,2,2])

                with c_prev:
                    if idx_atual > 0:
                        ant = FLUXO[idx_atual - 1]
                        if st.button(f"⬅️ Voltar para {STATUS_NOME[ant]}",
                                     key=f"prev_{p['id']}", use_container_width=True):
                            get_supabase().table("paradas").update(
                                {"status": ant}
                            ).eq("id", p["id"]).execute()
                            st.rerun()

                with c_next:
                    if idx_atual < len(FLUXO) - 1:
                        prox = FLUXO[idx_atual + 1]
                        if st.button(f"▶️ Avançar para {STATUS_NOME[prox]}",
                                     key=f"next_{p['id']}", use_container_width=True, type="primary"):
                            get_supabase().table("paradas").update(
                                {"status": prox}
                            ).eq("id", p["id"]).execute()
                            todos_emails = [u["email"] for u in listar_usuarios()]
                            notificar_avanco_fase(
                                emails           = todos_emails,
                                parada           = p["nome"],
                                fase_anterior    = p["status"],
                                nova_fase        = prox,
                                responsavel_acao = usuario["nome"],
                            )
                            st.success(f"✅ Avançado para {STATUS_NOME[prox]}! Equipe notificada.")
                            st.rerun()

                with c_edit:
                    with st.popover("✏️ Editar"):
                        with st.form(f"edit_p_{p['id']}"):
                            e_nome = st.text_input("Nome",        value=p["nome"])
                            e_resp = st.text_input("Responsável", value=p["responsavel"])
                            e_ini  = st.date_input("Início", value=date.fromisoformat(str(p["data_inicio"])))
                            e_fim  = st.date_input("Fim",    value=date.fromisoformat(str(p["data_fim"])))
                            if st.form_submit_button("💾 Salvar"):
                                get_supabase().table("paradas").update({
                                    "nome":        e_nome.strip(),
                                    "responsavel": e_resp.strip(),
                                    "data_inicio": str(e_ini),
                                    "data_fim":    str(e_fim),
                                }).eq("id", p["id"]).execute()
                                st.success("✅ Atualizado!")
                                st.rerun()
