from utils.supabase_client import get_supabase
from datetime import date


# ================================================================
# CONTRATOS
# ================================================================
def listar_contratos() -> list:
    sb = get_supabase()
    return sb.table("contratos").select("*").order("criado_em", desc=True).execute().data or []


def criar_contrato(dados: dict) -> dict:
    sb = get_supabase()
    resp = sb.table("contratos").insert(dados).execute()
    return resp.data[0] if resp.data else {}


# ================================================================
# PARADAS
# ================================================================
def listar_paradas(status=None) -> list:
    sb = get_supabase()
    q  = sb.table("paradas").select("*, contratos(codigo, nome)")
    if status:
        if isinstance(status, list):
            q = q.in_("status", status)
        else:
            q = q.eq("status", status)
    return q.order("criado_em", desc=True).execute().data or []


def criar_parada(dados: dict) -> dict:
    sb = get_supabase()
    resp = sb.table("paradas").insert(dados).execute()
    return resp.data[0] if resp.data else {}


def atualizar_status_parada(parada_id: str, novo_status: str):
    get_supabase().table("paradas").update({"status": novo_status}).eq("id", parada_id).execute()


def get_parada(parada_id: str) -> dict:
    resp = get_supabase().table("paradas").select("*, contratos(codigo, nome)").eq("id", parada_id).single().execute()
    return resp.data or {}


# ================================================================
# OCORRÊNCIAS
# ================================================================
def inserir_ocorrencias(ocorrencias: list) -> list:
    resp = get_supabase().table("ocorrencias").insert(ocorrencias).execute()
    return resp.data or []


def listar_ocorrencias_por_parada(parada_id: str) -> list:
    resp = get_supabase().table("ocorrencias").select("*").eq("parada_id", parada_id).order("criado_em").execute()
    return resp.data or []


def classificar_ocorrencia(ocorrencia_id: str, g: int, u: int, t: int):
    resultado = g * u * t
    classificacao = "baixo" if resultado <= 25 else "medio" if resultado <= 74 else "alto"
    get_supabase().table("ocorrencias").update(
        {"gravidade": g, "urgencia": u, "tendencia": t, "classificacao": classificacao}
    ).eq("id", ocorrencia_id).execute()


def get_ocorrencia(ocorrencia_id: str) -> dict:
    resp = get_supabase().table("ocorrencias").select("*").eq("id", ocorrencia_id).single().execute()
    return resp.data or {}


# ================================================================
# AÇÕES
# ================================================================
def criar_acao(dados: dict) -> dict:
    resp = get_supabase().table("acoes").insert(dados).execute()
    return resp.data[0] if resp.data else {}


def listar_acoes(filtros: dict = None) -> list:
    sb = get_supabase()
    q  = sb.table("acoes").select(
        "*, ocorrencias(area_setor, ocorrencia, resultado_gut, classificacao), paradas(nome)"
    )
    if filtros:
        if filtros.get("parada_ids"):
            q = q.in_("parada_id", filtros["parada_ids"])
        if filtros.get("responsavel_ids"):
            q = q.in_("responsavel_id", filtros["responsavel_ids"])
        if filtros.get("status"):
            q = q.in_("status", filtros["status"])
        if filtros.get("prazo_inicio"):
            q = q.gte("prazo", str(filtros["prazo_inicio"]))
        if filtros.get("prazo_fim"):
            q = q.lte("prazo", str(filtros["prazo_fim"]))
    data = q.order("prazo").execute().data or []
    if filtros and filtros.get("gut_niveis"):
        niveis = filtros["gut_niveis"]
        data = [a for a in data if (a.get("ocorrencias") or {}).get("classificacao") in niveis]
    return data


def atualizar_acao(acao_id: str, status: str, comentario: str = None):
    payload = {"status": status}
    if comentario:
        payload["comentarios"] = comentario
    if status == "concluido":
        payload["data_conclusao"] = str(date.today())
    get_supabase().table("acoes").update(payload).eq("id", acao_id).execute()


def deletar_acao(acao_id: str):
    get_supabase().table("acoes").delete().eq("id", acao_id).execute()


def listar_acoes_vencidas() -> list:
    resp = get_supabase().table("acoes").select("*, paradas(nome)").lt(
        "prazo", str(date.today())
    ).in_("status", ["pendente","em_andamento"]).execute()
    return resp.data or []


def listar_acoes_por_ocorrencia(ocorrencia_id: str) -> list:
    resp = get_supabase().table("acoes").select("*").eq("ocorrencia_id", ocorrencia_id).order("criado_em").execute()
    return resp.data or []


# ================================================================
# USUÁRIOS
# ================================================================
def listar_usuarios(perfil=None) -> list:
    sb = get_supabase()
    q  = sb.table("perfis_usuarios").select("*").eq("ativo", True)
    if perfil:
        if isinstance(perfil, list):
            q = q.in_("perfil", perfil)
        else:
            q = q.eq("perfil", perfil)
    return q.order("nome").execute().data or []


def get_usuario(user_id: str) -> dict:
    resp = get_supabase().table("perfis_usuarios").select("*").eq("id", user_id).single().execute()
    return resp.data or {}


def listar_emails_pmo() -> list:
    return [u["email"] for u in listar_usuarios(perfil=["pmo","admin"])]
