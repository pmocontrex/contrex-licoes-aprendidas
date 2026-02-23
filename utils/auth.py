import streamlit as st
from utils.supabase_client import get_supabase


def login(email: str, senha: str) -> dict:
    supabase = get_supabase()
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        session  = response.session
        user     = response.user
        perfil_resp = supabase.table("perfis_usuarios").select("*").eq("id", user.id).single().execute()
        perfil_data = perfil_resp.data
        st.session_state["session"]     = session
        st.session_state["user_id"]     = user.id
        st.session_state["user_email"]  = user.email
        st.session_state["user_nome"]   = perfil_data.get("nome", email)
        st.session_state["user_perfil"] = perfil_data.get("perfil", "setor")
        st.session_state["user_setor"]  = perfil_data.get("setor", "")
        st.session_state["user_ativo"]  = perfil_data.get("ativo", True)
        st.session_state["autenticado"] = True
        return perfil_data
    except Exception as e:
        raise ValueError(f"Falha no login: {str(e)}")


def logout():
    supabase = get_supabase()
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def get_perfil_atual() -> str:
    return st.session_state.get("user_perfil", "")


def verificar_permissao(perfis_permitidos: list):
    if not st.session_state.get("autenticado", False):
        st.error("Você precisa estar logado para acessar esta página.")
        st.stop()
    if get_perfil_atual() not in perfis_permitidos:
        st.error(f"🚫 Acesso negado. Perfis permitidos: {', '.join(perfis_permitidos)}.")
        st.stop()


def usuario_logado() -> dict:
    if not st.session_state.get("autenticado", False):
        return {}
    return {
        "id":     st.session_state.get("user_id"),
        "email":  st.session_state.get("user_email"),
        "nome":   st.session_state.get("user_nome"),
        "perfil": st.session_state.get("user_perfil"),
        "setor":  st.session_state.get("user_setor"),
        "ativo":  st.session_state.get("user_ativo"),
    }


def is_autenticado() -> bool:
    return st.session_state.get("autenticado", False)
