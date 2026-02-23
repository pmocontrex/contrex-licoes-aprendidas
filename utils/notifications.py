import smtplib
import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date


def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    try:
        cfg = st.secrets["smtp"]
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = cfg["from"]
        msg["To"]      = to_email
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        with smtplib.SMTP(cfg["host"], int(cfg["port"])) as server:
            server.ehlo()
            server.starttls()
            server.login(cfg["user"], cfg["password"])
            server.sendmail(cfg["user"], to_email, msg.as_string())
        return True
    except Exception as e:
        st.warning(f"⚠️ Falha ao enviar e-mail para {to_email}: {e}")
        return False


def _base_template(titulo: str, subtitulo: str, corpo: str, rodape: str = "") -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#F4F6F9;font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#F4F6F9;padding:30px 0;">
        <tr><td align="center">
          <table width="620" cellpadding="0" cellspacing="0"
                 style="background:white;border-radius:12px;overflow:hidden;
                        box-shadow:0 4px 20px rgba(0,0,0,0.10);">
            <tr>
              <td style="background:linear-gradient(135deg,#1B3A6B,#2D5AA0);
                         padding:30px 40px;border-bottom:4px solid #E87722;">
                <div style="color:white;font-size:22px;font-weight:bold;">
                  🏗️ CONTREX ENGENHARIA
                </div>
                <div style="color:rgba(255,255,255,0.75);font-size:13px;margin-top:4px;">
                  Sistema de Lições Aprendidas
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:30px 40px 10px;">
                <div style="font-size:20px;font-weight:bold;color:#1B3A6B;">{titulo}</div>
                <div style="font-size:14px;color:#666;margin-top:6px;">{subtitulo}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:10px 40px 30px;">{corpo}</td>
            </tr>
            <tr>
              <td style="background:#F8F9FA;padding:20px 40px;
                         border-top:1px solid #E9ECEF;text-align:center;">
                <div style="font-size:12px;color:#999;">
                  E-mail automático enviado por: <strong>{_remetente()}</strong><br>
                  Sistema de Lições Aprendidas — Contrex Engenharia<br>
                  {rodape}
                </div>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body></html>
    """


def _remetente() -> str:
    try:
        return st.secrets["smtp"]["from"]
    except Exception:
        return "Sistema Contrex"


def _info_box(label: str, valor: str, cor: str = "#1B3A6B") -> str:
    return f"""
    <div style="background:#F8F9FA;border-left:4px solid {cor};
                border-radius:6px;padding:12px 16px;margin:8px 0;">
      <div style="font-size:11px;color:#888;text-transform:uppercase;">{label}</div>
      <div style="font-size:15px;color:#333;margin-top:4px;font-weight:500;">{valor}</div>
    </div>
    """


def _botao(texto: str) -> str:
    return f"""
    <div style="text-align:center;margin:24px 0;">
      <span style="background:#E87722;color:white;padding:12px 32px;
                   border-radius:6px;font-size:15px;font-weight:bold;display:inline-block;">
        {texto}
      </span>
    </div>
    """


def _card_metrica(label: str, valor: int, cor: str) -> str:
    return f"""
    <td style="text-align:center;padding:0 6px;">
      <div style="background:white;border-radius:8px;padding:16px;
                  border-top:4px solid {cor};box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <div style="font-size:28px;font-weight:bold;color:{cor};">{valor}</div>
        <div style="font-size:12px;color:#888;margin-top:4px;">{label}</div>
      </div>
    </td>
    """


def _formatar_data(data_str: str) -> str:
    try:
        return date.fromisoformat(str(data_str)).strftime("%d/%m/%Y")
    except Exception:
        return str(data_str)


def _prazo_urgente(prazo_str: str) -> bool:
    try:
        return (date.fromisoformat(str(prazo_str)) - date.today()).days <= 7
    except Exception:
        return False


# ================================================================
# 1. PMO — setor enviou formulário
# ================================================================
def notificar_pmo_envio_formulario(
    email_pmo: str, nome_pmo: str,
    setor: str, parada: str, qtd_ocorrencias: int,
):
    corpo = f"""
    <p style="color:#333;font-size:15px;">Olá, <strong>{nome_pmo}</strong>!</p>
    <p style="color:#555;">Um novo formulário de lições aprendidas foi enviado e aguarda classificação GUT.</p>
    {_info_box("Setor que enviou", setor, "#1B3A6B")}
    {_info_box("Parada / Projeto", parada, "#E87722")}
    {_info_box("Ocorrências registradas", str(qtd_ocorrencias), "#28A745")}
    {_info_box("Data do envio", date.today().strftime("%d/%m/%Y"), "#666")}
    {_botao("🔬 Acessar Classificação GUT")}
    """
    html = _base_template(
        titulo="📋 Novo Formulário Recebido",
        subtitulo=f"O setor {setor} enviou {qtd_ocorrencias} ocorrência(s).",
        corpo=corpo,
    )
    return _send_email(email_pmo, f"[Contrex] Novo Formulário Recebido — {parada}", html)


# ================================================================
# 2. Responsável — ação atribuída
# ================================================================
def notificar_responsavel_acao(
    email: str, nome: str, acao: str,
    prazo: str, projeto: str, ocorrencia: str, nivel_gut: str,
):
    gut_cores = {
        "alto":  ("#FFEAEA", "#DC3545", "🔴 Alto"),
        "medio": ("#FFF8E1", "#856404", "🟡 Médio"),
        "baixo": ("#E8F5E9", "#28A745", "🟢 Baixo"),
    }
    bg, fg, label_gut = gut_cores.get(nivel_gut, ("#F0F0F0", "#333", "—"))
    urgente = _prazo_urgente(prazo)

    corpo = f"""
    <p style="color:#333;font-size:15px;">Olá, <strong>{nome}</strong>!</p>
    <p style="color:#555;">Você foi designado como responsável por uma ação no plano de melhorias.</p>
    {_info_box("Projeto / Parada", projeto, "#1B3A6B")}
    {_info_box("Ocorrência de origem", ocorrencia, "#666")}
    <div style="background:#F8F9FA;border-left:4px solid #E87722;
                border-radius:6px;padding:12px 16px;margin:8px 0;">
      <div style="font-size:11px;color:#888;text-transform:uppercase;">Prioridade GUT</div>
      <div style="margin-top:6px;">
        <span style="background:{bg};color:{fg};padding:4px 12px;
                     border-radius:20px;font-size:13px;font-weight:bold;">{label_gut}</span>
      </div>
    </div>
    <div style="background:#FFF3E0;border:1px solid #FFB74D;border-radius:8px;
                padding:16px;margin:16px 0;">
      <div style="font-size:12px;color:#E65100;font-weight:bold;margin-bottom:8px;">📌 AÇÃO ATRIBUÍDA</div>
      <div style="font-size:15px;color:#333;">{acao}</div>
    </div>
    <div style="background:{'#FFEAEA' if urgente else '#E3F2FD'};border-radius:8px;
                padding:16px;text-align:center;margin:16px 0;">
      <div style="font-size:13px;color:#666;">Prazo de conclusão</div>
      <div style="font-size:24px;font-weight:bold;
                  color:{'#DC3545' if urgente else '#1565C0'};">{_formatar_data(prazo)}</div>
      {'<div style="color:#DC3545;font-size:13px;margin-top:4px;">⚠️ Prazo em menos de 7 dias!</div>' if urgente else ''}
    </div>
    {_botao("📊 Acessar Painel de Acompanhamento")}
    """
    html = _base_template(
        titulo="📌 Nova Ação Atribuída a Você",
        subtitulo=f"Projeto: {projeto}",
        corpo=corpo,
    )
    return _send_email(email, f"[Contrex] Nova Ação Atribuída — {projeto}", html)


# ================================================================
# 3. Responsável — prazo vencendo (≤ 3 dias)
# ================================================================
def notificar_prazo_vencendo(email: str, nome: str, acoes_proximas: list):
    linhas = ""
    for a in acoes_proximas:
        dias = a["dias_restantes"]
        cor  = "#DC3545" if dias <= 1 else "#E65100" if dias <= 3 else "#856404"
        txt  = "HOJE" if dias == 0 else f"em {dias} dia(s)"
        linhas += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #EEE;color:#333;">{a['descricao']}</td>
          <td style="padding:10px;border-bottom:1px solid #EEE;color:#666;">{a['projeto']}</td>
          <td style="padding:10px;border-bottom:1px solid #EEE;text-align:center;">
            <span style="color:{cor};font-weight:bold;">
              {_formatar_data(a['prazo'])}<br><small>vence {txt}</small>
            </span>
          </td>
        </tr>
        """
    corpo = f"""
    <p style="color:#333;font-size:15px;">Olá, <strong>{nome}</strong>!</p>
    <p style="color:#555;">Você tem ações com prazo se encerrando nos próximos dias.</p>
    <table width="100%" cellpadding="0" cellspacing="0"
           style="border-collapse:collapse;border:1px solid #EEE;border-radius:8px;margin:16px 0;">
      <thead>
        <tr style="background:#1B3A6B;">
          <th style="padding:12px;color:white;text-align:left;font-size:13px;">Ação</th>
          <th style="padding:12px;color:white;text-align:left;font-size:13px;">Projeto</th>
          <th style="padding:12px;color:white;text-align:center;font-size:13px;">Prazo</th>
        </tr>
      </thead>
      <tbody>{linhas}</tbody>
    </table>
    {_botao("✏️ Atualizar Status das Ações")}
    """
    html = _base_template(
        titulo="⚠️ Ações com Prazo se Encerrando",
        subtitulo=f"Você tem {len(acoes_proximas)} ação(ões) que vencem em breve.",
        corpo=corpo,
        rodape="Lembrete automático enviado quando prazos estão próximos.",
    )
    return _send_email(email, "[Contrex] ⚠️ Ações com Prazo se Encerrando", html)


# ================================================================
# 4. Responsável — ação vencida
# ================================================================
def notificar_acao_vencida(email: str, nome: str, acoes_vencidas: list):
    linhas = ""
    for a in acoes_vencidas:
        linhas += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #EEE;color:#333;">{a['descricao']}</td>
          <td style="padding:10px;border-bottom:1px solid #EEE;color:#666;">{a['projeto']}</td>
          <td style="padding:10px;border-bottom:1px solid #EEE;text-align:center;">
            <span style="color:#DC3545;font-weight:bold;">{_formatar_data(a['prazo'])}</span><br>
            <small style="color:#DC3545;">{a['dias_atraso']} dia(s) de atraso</small>
          </td>
        </tr>
        """
    corpo = f"""
    <p style="color:#333;font-size:15px;">Olá, <strong>{nome}</strong>!</p>
    <div style="background:#FFEAEA;border:1px solid #DC3545;border-radius:8px;
                padding:16px;margin:16px 0;text-align:center;">
      <div style="font-size:18px;font-weight:bold;color:#DC3545;">
        🔴 {len(acoes_vencidas)} ação(ões) com prazo vencido
      </div>
      <div style="color:#B71C1C;font-size:14px;margin-top:6px;">
        Atualize o status ou entre em contato com o PMO imediatamente.
      </div>
    </div>
    <table width="100%" cellpadding="0" cellspacing="0"
           style="border-collapse:collapse;border:1px solid #EEE;border-radius:8px;margin:16px 0;">
      <thead>
        <tr style="background:#DC3545;">
          <th style="padding:12px;color:white;text-align:left;font-size:13px;">Ação</th>
          <th style="padding:12px;color:white;text-align:left;font-size:13px;">Projeto</th>
          <th style="padding:12px;color:white;text-align:center;font-size:13px;">Prazo / Atraso</th>
        </tr>
      </thead>
      <tbody>{linhas}</tbody>
    </table>
    {_botao("✏️ Atualizar Status Agora")}
    """
    html = _base_template(
        titulo="🔴 Ações com Prazo Vencido",
        subtitulo="Regularize as pendências o quanto antes.",
        corpo=corpo,
    )
    return _send_email(email, "[Contrex] 🔴 Ações com Prazo Vencido — Atenção Necessária", html)


# ================================================================
# 5. PMO — responsável atualizou status
# ================================================================
def notificar_atualizacao_status(
    email_pmo: str, nome_pmo: str, responsavel_nome: str,
    acao: str, status_anterior: str, novo_status: str,
    comentario: str, projeto: str,
):
    STATUS_LABEL = {
        "pendente":     ("🔵", "Pendente"),
        "em_andamento": ("🟠", "Em Andamento"),
        "concluido":    ("🟢", "Concluído"),
        "cancelado":    ("⚫", "Cancelado"),
    }
    icone_ant, label_ant = STATUS_LABEL.get(status_anterior, ("—", status_anterior))
    icone_nov, label_nov = STATUS_LABEL.get(novo_status,     ("—", novo_status))

    corpo = f"""
    <p style="color:#333;font-size:15px;">Olá, <strong>{nome_pmo}</strong>!</p>
    <p style="color:#555;">
      <strong>{responsavel_nome}</strong> atualizou o status de uma ação.
    </p>
    {_info_box("Projeto / Parada", projeto, "#1B3A6B")}
    <div style="background:#F8F9FA;border-radius:8px;padding:16px;margin:12px 0;">
      <div style="font-size:12px;color:#888;text-transform:uppercase;margin-bottom:8px;">Ação</div>
      <div style="font-size:15px;color:#333;">{acao}</div>
    </div>
    <table width="100%" cellpadding="0" cellspacing="0" style="margin:16px 0;">
      <tr>
        <td width="45%" style="background:#F8F9FA;border-radius:8px;padding:16px;text-align:center;">
          <div style="font-size:12px;color:#888;margin-bottom:8px;">STATUS ANTERIOR</div>
          <div style="font-size:18px;">{icone_ant} {label_ant}</div>
        </td>
        <td width="10%" style="text-align:center;font-size:24px;color:#999;">→</td>
        <td width="45%" style="background:#E8F5E9;border-radius:8px;padding:16px;text-align:center;">
          <div style="font-size:12px;color:#888;margin-bottom:8px;">NOVO STATUS</div>
          <div style="font-size:18px;">{icone_nov} {label_nov}</div>
        </td>
      </tr>
    </table>
    {f'''
    <div style="background:#FFF8E1;border-left:4px solid #FFC107;
                border-radius:6px;padding:12px 16px;margin:12px 0;">
      <div style="font-size:12px;color:#856404;font-weight:bold;margin-bottom:6px;">
        💬 COMENTÁRIO
      </div>
      <div style="font-size:14px;color:#333;">{comentario}</div>
    </div>
    ''' if comentario else ''}
    {_botao("📊 Ver no Painel")}
    """
    html = _base_template(
        titulo="🔄 Status de Ação Atualizado",
        subtitulo=f"Atualizado por {responsavel_nome} em {date.today().strftime('%d/%m/%Y')}",
        corpo=corpo,
    )
    return _send_email(email_pmo, f"[Contrex] Status Atualizado — {projeto}", html)


# ================================================================
# 6. Todos — parada avançou de fase
# ================================================================
def notificar_avanco_fase(
    emails: list, parada: str,
    fase_anterior: str, nova_fase: str, responsavel_acao: str,
):
    FASES = {
        "coleta":        ("🔵", "Coleta de Formulários"),
        "classificacao": ("🟡", "Classificação GUT"),
        "plano_acao":    ("🟠", "Plano de Ação"),
        "monitoramento": ("🟢", "Monitoramento"),
        "encerrada":     ("⚫", "Encerrada"),
    }
    INSTRUCOES = {
        "classificacao": "O PMO deve classificar as ocorrências utilizando a Matriz GUT.",
        "plano_acao":    "O PMO deve criar o plano de ação com responsáveis e prazos.",
        "monitoramento": "Os responsáveis devem atualizar o status das ações regularmente.",
        "encerrada":     "A parada foi encerrada. Todas as ações foram concluídas ou canceladas.",
    }
    icone_ant, label_ant = FASES.get(fase_anterior, ("—", fase_anterior))
    icone_nov, label_nov = FASES.get(nova_fase,     ("—", nova_fase))
    instrucao = INSTRUCOES.get(nova_fase, "Acesse o sistema para verificar as próximas etapas.")

    corpo = f"""
    <p style="color:#333;font-size:15px;">Prezados,</p>
    <p style="color:#555;">
      A parada <strong>{parada}</strong> avançou para uma nova fase do processo.
    </p>
    <table width="100%" cellpadding="0" cellspacing="0" style="margin:20px 0;">
      <tr>
        <td width="45%" style="background:#F8F9FA;border-radius:8px;padding:16px;text-align:center;">
          <div style="font-size:12px;color:#888;margin-bottom:8px;">FASE ANTERIOR</div>
          <div style="font-size:20px;">{icone_ant}</div>
          <div style="font-size:15px;font-weight:bold;color:#666;margin-top:4px;">{label_ant}</div>
        </td>
        <td width="10%" style="text-align:center;font-size:28px;color:#E87722;">→</td>
        <td width="45%" style="background:#E8F5E9;border:2px solid #28A745;
                                border-radius:8px;padding:16px;text-align:center;">
          <div style="font-size:12px;color:#888;margin-bottom:8px;">NOVA FASE</div>
          <div style="font-size:20px;">{icone_nov}</div>
          <div style="font-size:15px;font-weight:bold;color:#1B3A6B;margin-top:4px;">{label_nov}</div>
        </td>
      </tr>
    </table>
    <div style="background:#E3F2FD;border-radius:8px;padding:16px;margin:16px 0;">
      <div style="font-size:13px;font-weight:bold;color:#1565C0;margin-bottom:6px;">📋 Próximos passos</div>
      <div style="font-size:14px;color:#333;">{instrucao}</div>
    </div>
    {_info_box("Responsável pela transição", responsavel_acao, "#666")}
    {_info_box("Data", date.today().strftime("%d/%m/%Y"), "#666")}
    {_botao("🏗️ Acessar o Sistema")}
    """
    html = _base_template(
        titulo=f"🏗️ {parada} — Nova Fase",
        subtitulo=f"{label_ant} → {label_nov}",
        corpo=corpo,
    )
    sucessos = 0
    for email in emails:
        if _send_email(email, f"[Contrex] Parada Avançou de Fase — {parada}", html):
            sucessos += 1
    return sucessos


# ================================================================
# 7. PMO — resumo semanal
# ================================================================
def notificar_resumo_semanal(email_pmo: str, nome_pmo: str, dados: dict):
    acoes_venc_html = ""
    for a in dados.get("acoes_vencidas", [])[:10]:
        acoes_venc_html += f"""
        <tr>
          <td style="padding:8px;border-bottom:1px solid #EEE;color:#333;font-size:13px;">
            {a['descricao'][:60]}{'...' if len(a['descricao'])>60 else ''}
          </td>
          <td style="padding:8px;border-bottom:1px solid #EEE;color:#666;font-size:13px;">{a['projeto']}</td>
          <td style="padding:8px;border-bottom:1px solid #EEE;text-align:center;
                     color:#DC3545;font-size:13px;font-weight:bold;">{a['dias_atraso']}d</td>
        </tr>
        """
    paradas_html = "".join([
        f'<li style="color:#333;margin:4px 0;">{p}</li>'
        for p in dados.get("paradas_ativas", [])
    ])
    corpo = f"""
    <p style="color:#333;font-size:15px;">Olá, <strong>{nome_pmo}</strong>!</p>
    <p style="color:#555;">Aqui está o resumo semanal do sistema de Lições Aprendidas.</p>
    <table width="100%" cellpadding="0" cellspacing="0" style="margin:20px 0;">
      <tr>
        {_card_metrica("Total", dados.get('total_acoes',0), "#1B3A6B")}
        {_card_metrica("Pendentes", dados.get('pendentes',0), "#1565C0")}
        {_card_metrica("Em Andamento", dados.get('em_andamento',0), "#E65100")}
        {_card_metrica("Concluídas (semana)", dados.get('concluidas_semana',0), "#28A745")}
        {_card_metrica("Vencidas", dados.get('vencidas',0), "#DC3545")}
      </tr>
    </table>
    {f'''
    <div style="margin:20px 0;">
      <div style="font-size:15px;font-weight:bold;color:#DC3545;margin-bottom:10px;">
        🔴 Ações Vencidas ({len(dados.get("acoes_vencidas",[]))})
      </div>
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border-collapse:collapse;border:1px solid #EEE;border-radius:8px;">
        <thead>
          <tr style="background:#DC3545;">
            <th style="padding:10px;color:white;text-align:left;font-size:12px;">Ação</th>
            <th style="padding:10px;color:white;text-align:left;font-size:12px;">Projeto</th>
            <th style="padding:10px;color:white;text-align:center;font-size:12px;">Atraso</th>
          </tr>
        </thead>
        <tbody>{acoes_venc_html}</tbody>
      </table>
    </div>
    ''' if dados.get('acoes_vencidas') else ''}
    {f'<div style="margin:20px 0;"><div style="font-size:15px;font-weight:bold;color:#1B3A6B;margin-bottom:10px;">🏗️ Paradas Ativas</div><ul style="margin:0;padding-left:20px;">{paradas_html}</ul></div>' if dados.get('paradas_ativas') else ''}
    {_botao("📊 Acessar o Painel Completo")}
    """
    html = _base_template(
        titulo="📊 Resumo Semanal",
        subtitulo=f"Semana encerrada em {date.today().strftime('%d/%m/%Y')}",
        corpo=corpo,
        rodape="Resumo enviado automaticamente toda segunda-feira.",
    )
    return _send_email(email_pmo, "[Contrex] Resumo Semanal — Lições Aprendidas", html)
