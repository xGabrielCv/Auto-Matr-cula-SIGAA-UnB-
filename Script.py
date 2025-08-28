"""
⚠ ATENÇÃO ⚠

Este script está **intencionalmente incompleto** e requer que o usuário faça ajustes manuais
para funcionar corretamente. Alguns valores críticos, como parâmetros de navegação, índices
de colunas e XPaths de botões, foram deixados como placeholders.

Objetivo: Este script serve como **exercício educativo**. 

⚠ NÃO compartilhe suas credenciais pessoais. Use apenas para aprendizado e testes.
"""

"""
Projeto Final: Auto-Matrícula SIGAA (Versão 4.0)
→ O que este script faz:
1) Lê as suas credenciais e configurações diretamente desta seção.
2) Faz login no portal de autenticação da UnB.
3) Navega de forma robusta até a página de Matrícula Extraordinária.
4) Busca pela disciplina e turma que você configurou.
5) Se encontrar vagas, realiza a matrícula de forma prioritária e depois notifica.
6) Lida com erros, validações e reinicia a sessão automaticamente se necessário.
"""

from __future__ import annotations
import os
import time
import sys
import logging
import traceback
from collections import deque
import random

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
    UnexpectedAlertPresentException,
)
import requests

# ==================================================================
# ================== PAINEL DE CONTROLE DO SCRIPT ==================
# ==================================================================
# ATENÇÃO: Edite apenas os valores dentro das aspas.

# ------------------------------------------------------------------
# 1. SUAS INFORMAÇÕES PESSOAIS (OBRIGATÓRIO)
# ------------------------------------------------------------------
# ATENÇÃO: Use apenas para sua execução pessoal. Não compartilhe
# este arquivo com suas senhas.

# Seu usuário do SIGAA (geralmente a matrícula).
SIGAA_USER = "000000000"

# Sua senha do SIGAA.
SIGAA_PASS = "0000000000"

# Seu CPF (somente os números, sem pontos ou traços).
SIGAA_CPF = "00000000000"

# Sua data de nascimento no formato "dd/mm/aaaa".
SIGAA_NASCIMENTO = "00/00/0000"


# ------------------------------------------------------------------
# 2. DADOS DA DISCIPLINA ALVO (OBRIGATÓRIO)
# ------------------------------------------------------------------

# Código da disciplina que você deseja monitorar (ex: "FGA0235").
CODIGO_DISCIPLINA = "FGA0000"

# Turma da disciplina (ex: "01", "02", "S01").
TURMA = "00"


# ------------------------------------------------------------------
# 3. CONFIGURAÇÕES DE NOTIFICAÇÃO (OPCIONAL)
# ------------------------------------------------------------------

# Seu tópico secreto do app ntfy.sh para receber notificações no celular.
# Se não quiser usar, deixe como está: "seu-topico-secreto-aqui".
NTFY_TOPIC = "seu-topico-secreto-aqui"


# ------------------------------------------------------------------
# 4. COMPORTAMENTO DO ROBÔ (AVANÇADO)
# ------------------------------------------------------------------
# Na maioria dos casos, você não precisará alterar estas opções.

# Rodar o navegador de forma invisível (True) ou com a janela visível (False).
# Mude para `False` apenas para testar e ver o que o robô está fazendo.
HEADLESS = False

# MODO DE TESTE: Se True, o robô fará tudo, MENOS o clique final de
# confirmação da matrícula. Use True para testar com segurança.
# MUDE PARA FALSE PARA A MATRÍCULA REAL.
DRY_RUN = True

# Intervalo em segundos que o script espera antes de fazer uma nova verificação,
# caso não encontre vagas no ciclo atual.
INTERVALO_POLL = 40

# ==================================================================
# ============== FIM DO PAINEL DE CONTROLE =======================
# ==================================================================

"""
⚠ ATENÇÃO ⚠

Este script está **intencionalmente incompleto** e requer que o usuário faça ajustes manuais
para funcionar corretamente. Alguns valores críticos, como parâmetros de navegação, índices
de colunas e XPaths de botões, foram deixados como placeholders.

Objetivo: Este script serve como **exercício educativo**. 

⚠ NÃO compartilhe suas credenciais pessoais. Use apenas para aprendizado e testes.
"""

# --- Configurações Técnicas (REQUER ADAPTAÇÃO) ---
URL_LOGIN = "https://autenticacao.sua-universidade.br/sso-server/login?service=https://sig.sua-universidade.br/sigaa/login/cas"
URL_PORTAL_DISCENTE = "https://sig.sua-universidade.br/sigaa/portais/discente/discente.jsf"
URL_MATRICULA_EXTRAORDINARIA = "https://sig.sua-universidade.br/sigaa/graduacao/matricula/extraordinaria/matricula_extraordinaria.jsf"

CONFIG = {
    "DEFAULT_WAIT": 20,
    "MAX_TENTATIVAS_LOGIN": 3,
    "LIMITE_ALERTAS": 5,
    "PERIODO_LIMITACAO": 300,
}

if "seu_usuario_aqui" in SIGAA_USER or "sua_senha_aqui" in SIGAA_PASS or "00000000000" in SIGAA_CPF:
    print("[ERRO] Suas informações pessoais não foram preenchidas. Edite o 'Painel de Controle' no topo do script.")
    sys.exit(1)

# ========================= LOGGING ==============================
log = logging.getLogger("auto-matricula-sigaa")
log.setLevel(logging.INFO)
formatter = logging.Formatter(fmt="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
log.addHandler(stream_handler)
try:
    file_handler = logging.FileHandler("auto_matricula.log", mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)
except Exception as e:
    log.error("Não foi possível criar o arquivo de log: %s", e)

# ===================== FUNÇÕES DE ALERTA E UTILITÁRIOS =======================
_ts_alertas = deque()
def _pode_alertar() -> bool:
    agora = time.time()
    while _ts_alertas and _ts_alertas[0] < agora - CONFIG["PERIODO_LIMITACAO"]:
        _ts_alertas.popleft()
    if len(_ts_alertas) < CONFIG["LIMITE_ALERTAS"]:
        _ts_alertas.append(agora)
        return True
    return False

def _ntfy(titulo: str, mensagem: str) -> None:
    topic = NTFY_TOPIC.strip()
    if not topic or "seu-topico" in topic: return
    try:
        requests.post(f"https://ntfy.sh/{topic}", data=mensagem.encode("utf-8"), headers={"Title": titulo}, timeout=15)
    except Exception as e:
        log.warning("Falha ao enviar ntfy: %s", e)

def criar_driver() -> webdriver.Chrome:
    log.info("Inicializando o navegador...")
    opts = ChromeOptions()
    if HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1366,768")
    opts.add_argument("--lang=pt-BR")
    service = ChromeService()
    return webdriver.Chrome(service=service, options=opts)

def click_js(driver: webdriver.Chrome, el) -> None:
    driver.execute_script("arguments[0].click();", el)

def human_delay(min_sec=0.5, max_sec=1.5):
    time.sleep(random.uniform(min_sec, max_sec))

# ======================== FLUXO SIGAA ===========================
def login(driver: webdriver.Chrome) -> None:
    log.info("Abrindo tela de login centralizada…")
    driver.get(URL_LOGIN)
    wait = WebDriverWait(driver, CONFIG["DEFAULT_WAIT"])
    campo_user = wait.until(EC.presence_of_element_located((By.ID, "username")))
    campo_pass = wait.until(EC.presence_of_element_located((By.ID, "password")))
    btn_login  = wait.until(EC.element_to_be_clickable((By.NAME, "submit")))
    human_delay()
    campo_user.clear(); campo_user.send_keys(SIGAA_USER)
    human_delay()
    campo_pass.clear(); campo_pass.send_keys(SIGAA_PASS)
    human_delay()
    btn_login.click()
    try:
        log.info("Verificando se há uma tela de aviso...")
        wait_aviso = WebDriverWait(driver, 5)
        botao_continuar = wait_aviso.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Continuar >>']")))
        log.info("Tela de aviso detectada. Clicando em 'Continuar'...")
        human_delay()
        botao_continuar.click()
    except TimeoutException:
        log.info("Nenhuma tela de aviso detectada, seguindo para o portal.")
        pass
    log.info("Aguardando o carregamento completo do portal (pode demorar)...")
    wait_longo = WebDriverWait(driver, 60)
    wait_longo.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#portal-discente, #portal-docente")))
    log.info("Login efetuado com sucesso e portal carregado.")

def navegar_para_busca_turmas(driver: webdriver.Chrome) -> None:
    log.info("Iniciando navegação por requisição de rede direta...")
    wait = WebDriverWait(driver, CONFIG["DEFAULT_WAIT"])
    try:
        log.info("Coletando cookies e ViewState da sessão...")
        driver.get(URL_PORTAL_DISCENTE)
        wait.until(EC.presence_of_element_located((By.ID, "menu:form_menu_discente")))
        view_state = driver.find_element(By.NAME, "javax.faces.ViewState").get_attribute("value")
        session_id = driver.find_element(By.NAME, "id").get_attribute("value")
        cookies = {c['name']: c['value'] for c in driver.get_cookies()}
        
        # ALTERACAO 2: O parâmetro 'jscook_action' é a chave da navegação.
        jscook_action_param = "COLE_AQUI_O_VALOR_DO_JSCOOK_ACTION_CAPTurado"

        if "COLE_AQUI" in jscook_action_param:
            raise ValueError("O parâmetro 'jscook_action' não foi preenchido.")

        form_data = {
            'menu:form_menu_discente': 'menu:form_menu_discente',
            'id': session_id,
            'jscook_action': jscook_action_param,
            'javax.faces.ViewState': view_state,
        }
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        log.info("Enviando comando de navegação para o servidor...")
        response = requests.post(URL_PORTAL_DISCENTE, cookies=cookies, data=form_data, headers=headers, timeout=30)
        response.raise_for_status()
        log.info("Comando aceito. Navegando para a página final de matrícula...")
        driver.get(URL_MATRICULA_EXTRAORDINARIA)
        wait.until(EC.presence_of_element_located((By.ID, "form")))
        log.info("Página de busca de turmas carregada com SUCESSO!")
    except Exception as e:
        log.error("A navegação por requisição de rede falhou: %s", e)
        raise e

def preencher_filtros_busca(driver: webdriver.Chrome) -> None:
    log.info("Preenchendo filtros da busca com o código: %s", CODIGO_DISCIPLINA)
    wait = WebDriverWait(driver, CONFIG["DEFAULT_WAIT"])
    human_delay()
    wait.until(EC.element_to_be_clickable((By.ID, "form:checkCodigo"))).click()
    campo_codigo = wait.until(EC.presence_of_element_located((By.ID, "form:txtCodigo")))
    campo_codigo.clear()
    campo_codigo.send_keys(CODIGO_DISCIPLINA)
    log.info("Clicando em 'Buscar'...")
    human_delay()
    btn_buscar = wait.until(EC.element_to_be_clickable((By.ID, "form:buscar")))
    btn_buscar.click()
    try:
        WebDriverWait(driver, 3).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        log.warning("Alerta inesperado detectado após a busca: '%s'. Aceitando...", alert.text)
        alert.accept()
    except TimeoutException:
        log.info("Nenhum alerta inesperado após a busca.")
        pass
    wait.until(EC.presence_of_element_located((By.ID, "lista-turmas-extra")))
    log.info("Tabela de resultados carregada.")

def localizar_linha_disciplina(driver: webdriver.Chrome) -> Optional[dict]:
    wait = WebDriverWait(driver, CONFIG["DEFAULT_WAIT"])
    log.info("Procurando pela disciplina %s - Turma %s...", CODIGO_DISCIPLINA, TURMA)
    tabela = wait.until(EC.presence_of_element_located((By.ID, "lista-turmas-extra")))
    linhas = tabela.find_elements(By.XPATH, ".//tr")
    disciplina_encontrada = False
    linha_alvo = None
    for tr in linhas:
        try:
            texto_da_linha = tr.text
            if "disciplina" in tr.get_attribute("class") and CODIGO_DISCIPLINA in texto_da_linha:
                disciplina_encontrada = True
                continue
            if disciplina_encontrada:
                tds = tr.find_elements(By.TAG_NAME, "td")
                if len(tds) > 1 and f"Turma {TURMA}" in tds[1].text:
                    linha_alvo = tr
                    log.info("Linha da turma encontrada.")
                    break
                if "disciplina" in tr.get_attribute("class"):
                    break
        except StaleElementReferenceException:
            continue
    if not linha_alvo: return None
    tds = linha_alvo.find_elements(By.TAG_NAME, "td")
    
    # ALTERACAO 3: A ordem e o número de colunas pode variar.
    INDICE_COLUNA_VAGAS = 7 # TODO: 
    
    if len(tds) < INDICE_COLUNA_VAGAS + 1: return None
    def extrai_int(s: str) -> int:
        num = "".join(ch for ch in s if ch.isdigit())
        return int(num) if num else 0
    vagas = extrai_int(tds[INDICE_COLUNA_VAGAS].text)
    try:
        btn_matricular = linha_alvo.find_element(By.XPATH, ".//a[@title='SEU_TEXTO_DE_SELECAO_AQUI']") # TODO:
    except NoSuchElementException:
        btn_matricular = None
    return {"vagas_disponiveis": vagas, "elemento_matricular": btn_matricular}

def efetivar_matricula(driver: webdriver.Chrome, btn) -> bool:
    log.info("Iniciando processo de efetivação da matrícula...")
    wait = WebDriverWait(driver, CONFIG["DEFAULT_WAIT"])
    if not btn:
        log.error("Elemento de matrícula não foi passado para a função.")
        return False
    log.info("Clicando no botão 'Selecionar turma'...")
    human_delay()
    click_js(driver, btn)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.confirmaSenha")))
        log.info("Página de confirmação carregada.")
        try:
            campo_data = driver.find_element(By.XPATH, "//input[contains(@id, ':Data')]")
            log.info("Campo 'Data de Nascimento' encontrado. Preenchendo...")
            human_delay(0.5, 1.5)
            campo_data.send_keys(SIGAA_NASCIMENTO)
        except NoSuchElementException:
            log.info("Campo 'Data de Nascimento' não encontrado. Procurando por CPF...")
            try:
                campo_cpf = driver.find_element(By.XPATH, "//input[contains(@id, ':cpf')]")
                log.info("Campo 'CPF' encontrado. Preenchendo...")
                human_delay(0.5, 1.5)
                campo_cpf.send_keys(SIGAA_CPF)
            except NoSuchElementException:
                log.warning("Nenhum campo de confirmação (Data ou CPF) foi encontrado.")
        try:
            log.info("Preenchendo a senha de confirmação...")
            human_delay(0.5, 1.5)
            campo_senha = driver.find_element(By.XPATH, "//input[contains(@id, ':senha')]")
            campo_senha.send_keys(SIGAA_PASS)
        except NoSuchElementException:
            log.error("Campo de senha de confirmação não encontrado. Abortando matrícula.")
            return False
        if DRY_RUN:
            log.info("DRY_RUN ativo — matrícula NÃO será confirmada.")
            return True
        log.info("Clicando em 'Confirmar Matrícula'...")
        human_delay()
        btn_confirmar = driver.find_element(By.XPATH, "//input[@value='Confirmar Matrícula']")
        click_js(driver, btn_confirmar)
    except TimeoutException:
        log.error("A página de confirmação final não carregou a tempo.")
        return False
    try:
        WebDriverWait(driver, 8).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        log.info("Confirmando alert: %s", alert.text[:120])
        human_delay()
        alert.accept()
    except TimeoutException:
        log.info("Nenhum 'alert' de confirmação apareceu, continuando.")
    try:
        mensagem_sucesso = WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(@class,'info') or contains(@class,'success')]"))
        )
        log.info("SUCESSO! Mensagem de confirmação encontrada: '%s'", mensagem_sucesso.text)
        return True
    except TimeoutException:
        try:
            mensagem_erro = driver.find_element(By.XPATH, "//*[contains(@class,'Error') or contains(@class,'erro')]")
            log.error("FALHA! Mensagem de erro encontrada: '%s'", mensagem_erro.text)
            return False
        except NoSuchElementException:
            log.warning("AVISO: Não foi possível confirmar mensagem de SUCESSO ou de ERRO!")
            return False

# ======================== LOOP PRINCIPAL ========================
def main() -> None:
    tentativas_login = 0
    driver = None
    while True:
        try:
            if driver is None:
                driver = criar_driver()
                login(driver)
                navegar_para_busca_turmas(driver)
            
            preencher_filtros_busca(driver)
            dados = localizar_linha_disciplina(driver)

            if not dados:
                log.info("Disciplina/turma não encontrada na tabela. Atualizando a busca em %ss…", INTERVALO_POLL)
                time.sleep(INTERVALO_POLL)
                driver.refresh()
                continue

            vagas = dados["vagas_disponiveis"]
            log.info("Vagas disponíveis: %s", vagas)

            if vagas > 0:
                log.info("VAGA ENCONTRADA! Prioridade: TENTAR MATRÍCULA IMEDIATAMENTE.")
                sucesso = efetivar_matricula(driver, dados["elemento_matricular"])
                if _pode_alertar():
                    if sucesso:
                        log.info("Enviando notificação de SUCESSO na matrícula...")
                        _ntfy("SIGAA: MATRÍCULA EFETUADA!", f"Matrícula em {CODIGO_DISCIPLINA} - {TURMA} foi realizada com sucesso.")
                    elif not DRY_RUN:
                        log.info("Enviando notificação de FALHA na matrícula...")
                        _ntfy("SIGAA: FALHA NA MATRÍCULA!", f"O robô encontrou vaga em {CODIGO_DISCIPLINA} mas a matrícula FALHOU. Verifique o SIGAA!")
                if sucesso and not DRY_RUN:
                    log.info("Matrícula real bem-sucedida. Encerrando o script.")
                    break
                else:
                    log.info("Modo de teste ou falha na matrícula. O monitoramento continuará.")
                    log.warning("A falha na matrícula pode ter invalidado a página. Forçando reinicialização da sessão.")
                    driver.quit()
                    driver = None
                    time.sleep(INTERVALO_POLL)
                    continue
            
            else:
                log.info("Sem vagas. Nova verificação em %ss…", INTERVALO_POLL)
                time.sleep(INTERVALO_POLL)
        
        except (TimeoutException, WebDriverException, UnexpectedAlertPresentException) as e:
            log.warning("Falha de sessão ou carregamento (%s). Reinicializando o navegador…", type(e).__name__)
            if driver:
                try: driver.quit()
                except Exception: pass
            driver = None
            tentativas_login += 1
            if tentativas_login > CONFIG["MAX_TENTATIVAS_LOGIN"]:
                log.error("Excedeu o número máximo de tentativas de login. Abortando.")
                break
            time.sleep(5)
        except KeyboardInterrupt:
            log.info("Encerrado pelo usuário.")
            break
        except Exception:
            log.error("Erro inesperado no loop principal:\n%s", traceback.format_exc())
            traceback.print_exc()
            time.sleep(15)
    
    if driver:
        try: driver.quit()
        except Exception: pass

if __name__ == "__main__":
    main()

    """
⚠ ATENÇÃO ⚠

Este script está **intencionalmente incompleto** e requer que o usuário faça ajustes manuais
para funcionar corretamente. Alguns valores críticos, como parâmetros de navegação, índices
de colunas e XPaths de botões, foram deixados como placeholders.

Objetivo: Este script serve como **exercício educativo**. 

⚠ NÃO compartilhe suas credenciais pessoais. Use apenas para aprendizado e testes.
"""