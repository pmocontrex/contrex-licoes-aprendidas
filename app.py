import streamlit as st
from utils.auth import login, logout, is_autenticado, usuario_logado, get_perfil_atual
from utils.db_queries import listar_paradas

st.set_page_config(
    page_title="Contrex — Lições Aprendidas",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

STYLE = """
<style>
    .page-header { background:linear-gradient(135deg,#1B3A6B,#2D5AA0);color:white;
                   padding:1.5rem 2rem;border-radius:10px;margin-bottom:2rem;
                   border-left:5px solid #E87722; }
    .metric-card { background:white;border-radius:10px;padding:1.5rem;
                   border-top:4px solid #E87722;
                   box-shadow:0 2px 8px rgba(0,0,0,0.08);text-align:center; }
    .gut-alto  { background:#FFEAEA;color:#DC3545;padding:3px 10px;border-radius:20px;font-weight:bold; }
    .gut-medio { background:#FFF8E1;color:#856404;padding:3px 10px;border-radius:20px;font-weight:bold; }
    .gut-baixo { background:#E8F5E9;color:#28A745;padding:3px 10px;border-radius:20px;font-weight:bold; }
    .status-pendente  { background:#E3F2FD;color:#1565C0;padding:2px 8px;border-radius:12px; }
    .status-andamento { background:#FFF3E0;color:#E65100;padding:2px 8px;border-radius:12px; }
    .status-concluido { background:#E8F5E9;color:#2E7D32;padding:2px 8px;border-radius:12px; }
    .status-cancelado { background:#EEEEEE;color:#616161;padding:2px 8px;border-radius:12px; }
    section[data-testid="stSidebar"] { background-color:#1B3A6B !important; }
    section[data-testid="stSidebar"] * { color:white !important; }
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)


def tela_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;padding:40px 0 20px;">
          <div style="background:#1B3A6B;color:white;padding:20px 40px;border-radius:10px;
                      display:inline-block;border-bottom:4px solid #E87722;">
            <h1 style="margin:0;font-size:2rem;">🏗️ CONTREX ENGENHARIA</h1>
            <p style="margin:5px 0 0;opacity:0.8;">Sistema de Lições Aprendidas</p>
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("Acesso ao Sistema")
        with st.form("form_login"):
            email = st.text_input("📧 E-mail", placeholder="usuario@contrex.com.br")
            senha = st.text_input("🔒 Senha", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")
        if submitted:
            if not email or not senha:
                st.error("Preencha e-mail e senha.")
            else:
                with st.spinner("Autenticando..."):
                    try:
                        login(email, senha)
                        st.rerun()
                    except ValueError as e:
                        st.error(f"❌ {e}")


def tela_home():
    usuario = usuario_logado()
    perfil  = get_perfil_atual()

    with st.sidebar:
        st.markdown(f"""
        <div style="padding:10px 0;">
          <h3 style="margin:0;color:white;">🏗️ CONTREX</h3>
          <p style="margin:0;opacity:0.8;font-size:13px;">Lições Aprendidas</p>
        </div>
        <hr style="border-color:rgba(255,255,255,0.3);">
        <p style="margin:0;font-size:14px;"><b>👤 {usuario.get('nome','')}</b></p>
        <p style="margin:0;font-size:12px;opacity:0.8;">{perfil.upper()}</p>
        """, unsafe_allow_html=True)

        paradas_ativas = listar_paradas(
            status=["coleta","classificacao","plano_acao","monitoramento"]
        )
        if paradas_ativas:
            st.markdown("<hr style='border-color:rgba(255,255,255,0.3);'>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:12px;opacity:0.8;margin:0;'>PARADAS ATIVAS</p>",
                        unsafe_allow_html=True)
            for p in paradas_ativas[:5]:
                st.markdown(f"<p style='font-size:13px;margin:2px 0;'>📍 {p['nome']}</p>",
                            unsafe_allow_html=True)

        st.markdown("<hr style='border-color:rgba(255,255,255,0.3);'>", unsafe_allow_html=True)
        if st.button("🚪 Sair", use_container_width=True):
            logout()

    st.markdown(f"""
    <div class="page-header">
      <h1 style="margin:0;">🏗️ Bem-vindo, {usuario.get('nome','')}!</h1>
      <p style="margin:5px 0 0;opacity:0.9;">
        Contrex Engenharia — Sistema de Lições Aprendidas em Paradas Gerais
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Acesso Rápido")

    modulos = []
    if perfil in ("setor","pmo","admin"):
        modulos.append(("📋", "Formulário do Setor",
                         "Registre ocorrências e lições aprendidas da sua área."))
    if perfil in ("pmo","admin"):
        modulos.append(("🔬", "Classificação GUT",
                         "Classifique as ocorrências usando a Matriz GUT."))
        modulos.append(("📝", "Plano de Ação",
                         "Crie e atribua ações corretivas para cada ocorrência."))
    modulos.append(("📊", "Painel de Acompanhamento",
                     "Monitore o andamento das ações em tempo real."))
    if perfil in ("pmo","admin"):
        modulos.append(("⚙️", "Administração",
                         "Gerencie usuários, contratos e paradas."))

    cols = st.columns(len(modulos))
    for col, (icon, titulo, desc) in zip(cols, modulos):
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div style="font-size:3rem;">{icon}</div>
              <h4 style="color:#1B3A6B;margin:10px 0 5px;">{titulo}</h4>
              <p style="color:#666;font-size:13px;margin:0;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.info("💡 Utilize o menu lateral para navegar entre os módulos do sistema.")


if not is_autenticado():
    tela_login()
else:
    tela_home()
