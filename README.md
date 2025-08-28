# Auto-Matrícula SIGAA (UnB) 🤖

*Um robô em Python que automatiza o processo de login e matrícula extraordinária no SIGAA da UnB, com notificações em tempo real para o celular.*

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![Selenium](https://img.shields.io/badge/Selenium-4-green?style=for-the-badge&logo=selenium)

> [!WARNING]
> ### ⚠️ Aviso Importante e Declaração de Responsabilidade
> 
> **1. CÓDIGO COMO FERRAMENTA EDUCACIONAL**
> - Este repositório é fornecido como uma **prova de conceito** e **template educacional**.
> - Para funcionar corretamente, é necessário que o usuário final revise, ajuste ou complete os seletores e a lógica para a versão atual do SIGAA.
> - Este passo reforça que **o usuário é o único responsável** pela execução do script.
> 
> **2. PROJETO EDUCACIONAL**
> - O script foi desenvolvido **exclusivamente para fins de estudo** e demonstra técnicas avançadas de automação web.
> 
> **3. VIOLAÇÃO DOS TERMOS DE SERVIÇO**
> - O uso de qualquer meio automatizado para acessar sistemas autenticados, como o SIGAA, **pode violar os Termos de Serviço da universidade**.
> - O autor **não endossa nem se responsabiliza** por usos que contravenham as regras institucionais.
> 
> **4. USO POR SUA CONTA E RISCO**
> - Você assume **total responsabilidade** por qualquer consequência acadêmica ou técnica derivada do uso deste código.
> 
> **5. IMPACTO COLETIVO**
> - Uso massivo e irresponsável pode sobrecarregar os servidores do SIGAA, prejudicando toda a comunidade acadêmica.
> - Utilize o script com **moderação e ética**.
> 
> **6. ALTERNATIVA DE BAIXO RISCO (APENAS MONITORAMENTO)**
> - Se o objetivo é apenas receber alertas de vagas, sem efetivar matrícula, recomenda-se usar projetos que monitorem **apenas páginas públicas**.
> - Essa abordagem **não requer login**, reduzindo significativamente o risco de violação de termos.
> - [Projeto de Monitoramento Seguro](https://github.com/xGabrielCv/Monitorador-Vagas-SIGAA-Unb)


---

### 📌 Principais Funcionalidades

-   ✅ **Login Automatizado:** Entra de forma segura no sistema de autenticação central da UnB (SSO).
-   ✅ **Navegação Robusta:** Contorna o complexo menu JavaScript do SIGAA utilizando requisições de rede diretas, garantindo acesso estável à página de matrícula.
-   ✅ **Monitoramento Contínuo:** Verifica a disciplina e turma configuradas em intervalos de tempo definidos.
-   ✅ **Matrícula Prioritária:** Ao encontrar uma vaga, a prioridade máxima é realizar a matrícula imediatamente para garantir a vaga, notificando o resultado apenas depois.
-   ✅ **Confirmação Inteligente:** Lida com as diferentes telas de confirmação do SIGAA, preenchendo CPF ou Data de Nascimento conforme a necessidade.
-   ✅ **Notificações em Tempo Real:** Envia alertas para o celular via [ntfy.sh](https://ntfy.sh/) informando sobre sucesso ou falha na matrícula.
-   ✅ **Reinicialização Automática:** Em caso de falha de sessão, erro de rede ou instabilidade do SIGAA, o robô reinicia o ciclo do zero, garantindo funcionamento contínuo.
-   ✅ **Modo de Teste Seguro (`DRY_RUN`):** Permite testar todo o fluxo sem efetivar o clique final de confirmação da matrícula.
-   ✅ **Comportamento “Humano”:** Adiciona pequenas pausas aleatórias para simular um comportamento de navegação menos robótico e mais discreto.
-   ✅ **Logging Completo:** Salva todas as ações em um arquivo `auto_matricula.log` para fácil depuração e acompanhamento histórico.

### ✨ Como Funciona (A Mágica por Trás)

A parte mais complexa deste projeto foi a navegação pós-login, que foi resolvida com uma técnica avançada que bypassa a interface do usuário:

1.  O robô faz login com o `Selenium` para obter uma sessão válida no navegador.
2.  Ele "rouba" as chaves dessa sessão (os `cookies` e o `ViewState` da página).
3.  Usando a biblioteca `requests`, ele envia um comando de rede direto para o servidor, replicando exatamente a requisição que o navegador faria ao clicar no menu do SIGAA.
4.  Com a sessão agora validada pelo servidor para o módulo de matrícula, ele pode navegar diretamente para a página final sem ser bloqueado.

### ⚙️ Pré-requisitos

* **Python 3.9+**
* **Google Chrome** instalado no computador.

As bibliotecas Python necessárias podem ser instaladas com um único comando:
```bash
pip install selenium requests
```
> [!NOTE]
> O `chromedriver` é gerenciado **automaticamente** pela versão moderna do Selenium. Você **não precisa** baixar ou gerenciar o `chromedriver` manualmente.

### 📝 Configuração

Todo o script é configurado em um "Painel de Controle" de fácil edição no topo do arquivo `.py`.

#### 1. Informações Pessoais (Obrigatório)
```python
SIGAA_USER = "211073798"
SIGAA_PASS = "sua_senha"
SIGAA_CPF = "03678904432"
SIGAA_NASCIMENTO = "10/01/2005"
```

#### 2. Dados da Disciplina Alvo (Obrigatório)
```python
CODIGO_DISCIPLINA = "FGA0060"
TURMA = "03"
```

#### 3. Configurações de Notificação (Opcional)
```python
# Baixe o app ntfy no seu celular, crie um tópico secreto
# (ex: meu-alerta-sigaa-12345), inscreva-se e adicione o nome aqui.
NTFY_TOPIC = "meu-alerta-sigaa-12345"
```

#### 4. Comportamento do Robô (Avançado)
```python
HEADLESS = False      # True: navegador invisível; False: visível
DRY_RUN = True        # True: testa sem matrícula real; False: matrícula real
INTERVALO_POLL = 15   # Tempo entre verificações em segundos
```
> [!IMPORTANT]
> Mantenha `DRY_RUN = True` durante todos os testes. Só altere para `False` quando tiver certeza absoluta que o script está funcionando como esperado.

### 🚀 Como Executar

1.  Faça o download do script `Script.py`.
2.  Instale as dependências: `pip install selenium requests`.
3.  Abra o arquivo e preencha o **Painel de Controle** com seus dados.
4.  **Teste** o script com as configurações `DRY_RUN = True` e `HEADLESS = False` para assistir o robô em ação.
5.  Quando estiver pronto para a matrícula real, altere:
    * `DRY_RUN = False`
    * `HEADLESS = True` (para rodar em segundo plano)
6.  Abra um terminal na pasta do script e execute:
    ```bash
    python Script.py
    ```

### 📋 Logging

Todas as ações são salvas em `auto_matricula.log` na mesma pasta do script. O log registra:
* Status de login
* Navegação e carregamento de páginas
* Busca de disciplinas e turmas
* Vagas encontradas
* Resultados de matrícula (sucesso ou falha)
* Alertas enviados via ntfy
* Erros, exceções e reinicializações automáticas

É extremamente útil para depuração, para acompanhar o que o robô fez durante a noite ou para analisar falhas.
