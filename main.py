"""
Trabalho 3 - Simulador do Algoritmo do Banqueiro (Versão 1 e Versão 2)
Disciplina: Sistemas Operacionais

Versão 1: Algoritmo do Banqueiro (Dijkstra, 1965) - evita impasses verificando
          se o estado resultante permanece seguro antes de conceder recursos.
Versão 2: Alocação Ingênua / FCFS (First-Come, First-Served) - concede qualquer
          requisição que caiba no saldo disponível no momento, sem verificar
          segurança, demonstrando como o sistema entra em estado inseguro e
          pode chegar a deadlock.

Por que FCFS? É o oposto mais simples e didático do Banqueiro: atende por ordem
de chegada ("tem no cofre, entrega") e não faz nenhum teste de segurança. Sobre
a mesma entrada do T4, o Banqueiro nega REQ B 1 e preserva o sistema, enquanto o
FCFS concede, reduz o disponível para 1 e permite que todos os processos fiquem
bloqueados em deadlock.

Uso:
    python main.py            # demonstração/comparação (padrão)
    python main.py --testes   # apenas os testes obrigatórios T1 a T5
"""

import argparse  # Leitura de argumentos da linha de comando (--testes / -t)
import copy      # Cópia profunda (deepcopy) para simular alocações sem alterar o estado real
import json      # Leitura dos arquivos de estado no formato JSON (Opção 3 do enunciado)
from pathlib import Path  # Manipulação segura de caminhos de arquivos entre SOs

# Importa utilitários de formatação visual (separados da lógica do simulador)
from estilo import (
    AMARELO,
    AZUL,
    CIANO,
    NEGRITO,
    VERDE,
    VERMELHO,
    colorir_status,
    estilizar,
    imprimir_secao,
)

# Diretório onde ficam os arquivos de entrada dos testes (t1.json..t3.json e req_*.txt)
TESTES_DIR = Path(__file__).resolve().parent / "testes"


# =============================================================================
# 1. LEITURA DE ENTRADAS E FUNÇÕES AUXILIARES
# =============================================================================

def ler_input(caminho: Path) -> tuple[int, list[dict]]:
    """
    Lê o arquivo de estado inicial no formato JSON (Opção 3 do trabalho).

    Estrutura esperada no JSON:
        {
            "total": 10,
            "processos": [
                {"nome": "A", "possui": 1, "maximo": 6},
                ...
            ]
        }

    Retorna uma tupla (total_de_recursos, lista_de_processos).
    """
    with open(caminho, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    total = dados["total"]
    processos = dados["processos"]

    return total, processos


def ler_requisicoes(caminho: Path) -> list[tuple[str, int]]:
    """
    Lê um arquivo de requisições no formato definido pelo enunciado:
        REQ <NOME_DO_PROCESSO> <QUANTIDADE>
        Exemplo: REQ B 1

    Linhas em branco e comentários iniciados com '#' são ignorados.
    Retorna uma lista de tuplas (nome_processo, quantidade).
    """
    requisicoes: list[tuple[str, int]] = []
    with open(caminho, "r", encoding="utf-8") as f:
        for num_linha, linha in enumerate(f, start=1):
            linha = linha.strip()
            # Ignora linhas vazias e comentários nos arquivos de teste
            if not linha or linha.startswith("#"):
                continue

            partes = linha.split()
            # Valida se a linha segue exatamente o padrão "REQ <PROCESSO> <QTD>"
            if len(partes) != 3 or partes[0].upper() != "REQ":
                raise ValueError(
                    f"Linha {num_linha} inválida: '{linha}'. Formato esperado: REQ <PROCESSO> <QTD>"
                )

            nome = partes[1]
            qtd = int(partes[2])
            requisicoes.append((nome, qtd))
    return requisicoes


def calcular_disponivel(total: int, processos: list[dict]) -> int:
    """
    Calcula quantas unidades de recurso ainda estão livres no "cofre" do banqueiro.

    Fórmula do enunciado: Disponível = TOTAL - soma(possui de todos os processos).
    Exemplo (T2): Total = 10, Alocados = 1+1+2+4 = 8  ->  Disponível = 2.
    """
    total_possuido = sum(p["possui"] for p in processos)
    return total - total_possuido


def formatar_sequencia(sequencia: list[str]) -> str:
    """Formata a sequência segura (ex.: ['C', 'D', 'A', 'B'] -> 'C, D, A, B')."""
    return ", ".join(sequencia) if sequencia else "nenhum processo pendente"


def imprimir_requisicao(indice: int, total: int, mensagem: str) -> None:
    """Imprime uma requisição numerada (ex.: [1/5]), destacando palavras-chave."""
    etiqueta = estilizar(f"  [{indice}/{total}]", NEGRITO, CIANO)
    print(f"{etiqueta} {colorir_status(mensagem)}")


def validar_estado(total: int, processos: list[dict]) -> None:
    """
    Verifica a consistência dos dados de entrada antes de iniciar a simulação.

    Garante que:
    - Não existem valores negativos;
    - Nenhum processo possui mais recursos do que seu máximo declarado;
    - A soma de recursos alocados não ultrapassa o total existente no sistema.
    """
    if total < 0:
        raise ValueError("Total de recursos não pode ser negativo.")

    soma_possui = 0
    for p in processos:
        nome = p["nome"]
        possui = p["possui"]
        maximo = p["maximo"]

        if possui < 0 or maximo < 0:
            raise ValueError(f"Processo '{nome}' possui valores negativos.")
        if possui > maximo:
            raise ValueError(
                f"Processo '{nome}' possui ({possui}) mais que o máximo ({maximo})."
            )

        soma_possui += possui

    if soma_possui > total:
        raise ValueError(
            f"Soma alocada ({soma_possui}) excede o total de recursos ({total})."
        )


# =============================================================================
# 2. VERSÃO 1 - ALGORITMO DO BANQUEIRO (DIJKSTRA, 1965)
# =============================================================================

def esta_seguro(total: int, processos: list[dict]) -> tuple[bool, list[str]]:
    """
    Requisito 1 da Versão 1: Verificação de Estado Seguro.

    Um estado é considerado SEGURO se existir pelo menos uma ordem (sequência
    segura) em que todos os processos ativos possam receber o restante de seus
    recursos, concluir e devolver o que possuem ao cofre.

    Passos do algoritmo:
    1. Inicializa 'work' (saldo simulado) com o total disponível atual.
    2. Procura um processo ainda não finalizado cuja necessidade (máximo - possui)
       seja menor ou igual a 'work'.
    3. Se encontrar, simula sua conclusão: soma os recursos que ele já possuía
       de volta em 'work', marca como finalizado e adiciona na sequência segura.
    4. Repete até todos finalizarem (SEGURO) ou até nenhuma iteração conseguir
       finalizar mais ninguém (INSEGURO).
    """
    # 'work' representa os recursos disponíveis conforme simulamos a conclusão dos processos
    work = calcular_disponivel(total, processos)
    if work < 0:
        return False, []

    # Processos já concluídos não precisam mais entrar na sequência segura.
    ativos = [p for p in processos if not p.get("concluido")]
    n = len(ativos)
    finalizado = [False] * n
    sequencia: list[str] = []

    # Tenta encontrar uma ordem que consiga finalizar todos os 'n' processos ativos
    while len(sequencia) < n:
        progrediu = False  # Controla se algum processo conseguiu concluir nesta passagem

        for i, p in enumerate(ativos):
            # Necessidade = quantos recursos ainda faltam para o processo atingir o máximo
            necessidade = p["maximo"] - p["possui"]

            # Se o processo ainda não terminou e o saldo atual cobre o que ele precisa:
            if not finalizado[i] and necessidade <= work:
                # Simula o término: ao concluir, o processo devolve tudo que já possuía
                work += p["possui"]
                finalizado[i] = True
                sequencia.append(p["nome"])
                progrediu = True

        # Se percorreu todos os processos e nenhum pôde concluir, não há saída segura
        if not progrediu:
            return False, []

    # Todos os processos ativos entraram na sequência -> estado SEGURO
    return True, sequencia


def solicitar_recurso(
    total: int, processos: list[dict], nome_processo: str, quantidade: int
) -> tuple[bool, str]:
    """
    Requisito 2 da Versão 1: Processamento de Requisição (Algoritmo do Banqueiro).

    Fluxo de decisão:
    1. Valida se o processo existe e se a quantidade é válida (não excede o máximo).
    2. Verifica se há recursos disponíveis suficientes no momento.
    3. Simula a concessão em uma cópia do estado (sem mexer no estado real).
    4. Executa 'esta_seguro()' sobre o estado simulado:
       - Se resultar em estado INSEGURO -> NEGA a requisição (rollback implícito,
         pois o estado original não foi alterado).
       - Se resultar em estado SEGURO   -> CONCEDE e efetiva no estado real.
    5. Caso o processo atinja seu máximo após a concessão, ele conclui e devolve
       todos os seus recursos ao sistema.
    """
    # 1. Busca o processo pelo nome
    processo = next((p for p in processos if p["nome"] == nome_processo), None)
    if processo is None:
        return False, (
            f"REQ {nome_processo} {quantidade} -> NEGADA "
            f"(processo '{nome_processo}' não existe)"
        )

    necessidade = processo["maximo"] - processo["possui"]

    # 2. Validações de integridade do pedido
    if quantidade <= 0:
        return False, (
            f"REQ {nome_processo} {quantidade} -> NEGADA (quantidade inválida)"
        )
    if quantidade > necessidade:
        return False, (
            f"REQ {nome_processo} {quantidade} -> NEGADA "
            "(excede o máximo declarado pelo processo)"
        )

    # 3. Verifica se o cofre tem saldo imediato para atender o pedido
    disponivel = calcular_disponivel(total, processos)
    if quantidade > disponivel:
        return False, (
            f"REQ {nome_processo} {quantidade} -> NEGADA "
            f"(recursos disponíveis insuficientes: {disponivel})"
        )

    # 4. Simulação hipotética ("e se eu emprestar agora?"):
    #    Usa deepcopy para testar o impacto da alocação sem alterar o estado real.
    estado_simulado = copy.deepcopy(processos)
    for p in estado_simulado:
        if p["nome"] == nome_processo:
            p["possui"] += quantidade
            break

    # 5. Testa se o estado após o empréstimo hipotético continua SEGURO
    seguro, sequencia = esta_seguro(total, estado_simulado)
    if not seguro:
        # Rollback automático: como só alteramos 'estado_simulado', 'processos' segue intacto
        return False, (
            f"REQ {nome_processo} {quantidade} -> NEGADA (estado resultante inseguro)"
        )

    # 6. Estado resultante é seguro -> efetiva a concessão no estado real
    processo["possui"] += quantidade
    seq_str = formatar_sequencia(sequencia)

    # Se o processo atingiu o máximo, conclui sua tarefa e devolve todos os recursos ao cofre
    if processo["possui"] == processo["maximo"]:
        processo["possui"] = 0
        processo["maximo"] = 0
        processo["concluido"] = True

    return True, (
        f"REQ {nome_processo} {quantidade} -> CONCEDIDA "
        f"(sequência segura: {seq_str})"
    )


def executar_arquivos(caminho_json: Path, caminho_req: Path) -> None:
    """
    Função auxiliar para executar a Versão 1 a partir de quaisquer dois arquivos:
    um JSON de estado inicial e um TXT de requisições.

    Lê o JSON, valida o estado inicial, exibe a tabela de recursos, verifica se o
    estado inicial já é seguro e processa cada linha `REQ <processo> <quantidade>`.
    """
    total, processos = ler_input(caminho_json)
    validar_estado(total, processos)
    requisicoes = ler_requisicoes(caminho_req)

    print(estilizar(f"Arquivo de estado: {caminho_json}", NEGRITO))
    print(estilizar(f"Arquivo de requisições: {caminho_req}", NEGRITO))
    exibir_resumo_estado(total, processos)

    seguro, sequencia = esta_seguro(total, processos)
    if seguro:
        print(
            colorir_status(
                f"Estado inicial: SEGURO (sequência segura: {', '.join(sequencia)})"
            )
        )
    else:
        print(colorir_status("Estado inicial: INSEGURO (não há sequência segura)"))

    print(estilizar("--- Processando requisições ---", NEGRITO, CIANO))
    for indice, (nome, quantidade) in enumerate(requisicoes, start=1):
        _, mensagem = solicitar_recurso(total, processos, nome, quantidade)
        imprimir_requisicao(indice, len(requisicoes), mensagem)

    print()
    print(estilizar("--- Estado final ---", NEGRITO, CIANO))
    exibir_resumo_estado(total, processos)


# =============================================================================
# 3. VERSÃO 2 - ALOCAÇÃO INGÊNUA / FCFS (CONTRASTE QUE DEMONSTRA O DEADLOCK)
# =============================================================================

def solicitar_recurso_fcfs(
    total: int,              # Total de recursos existentes no sistema (ex.: 10)
    processos: list[dict],   # Lista de processos com posse atual e máximo
    nome_processo: str,      # Nome do processo que está solicitando recursos (ex.: "B")
    quantidade: int,         # Quantidade solicitada (ex.: 1)
    bloqueados: set[str],    # Conjunto dos processos atualmente travados aguardando recurso
) -> tuple[bool, str]:
    """
    Versão 2 - Alocação Ingênua / FCFS (First-Come, First-Served).

    Diferença central em relação ao Algoritmo do Banqueiro:
    - O Banqueiro testa se o estado futuro será SEGURO antes de conceder.
    - O FCFS olha apenas o presente: "se há saldo disponível no cofre agora,
      concede imediatamente". Se não há saldo, o processo fica BLOQUEADO
      esperando outros processos devolverem recursos.

    Essa ausência de prevenção permite que o sistema entre em estado inseguro
    e, na sequência de pedidos seguinte, trave todos os processos em DEADLOCK.
    """
    # Validação de existência do processo
    processo = next((p for p in processos if p["nome"] == nome_processo), None)
    if processo is None:
        return False, (
            f"REQ {nome_processo} {quantidade} -> ERRO "
            f"(processo '{nome_processo}' não existe)"
        )

    necessidade = processo["maximo"] - processo["possui"]

    # Validação da quantidade solicitada
    if quantidade <= 0:
        return False, f"REQ {nome_processo} {quantidade} -> ERRO (quantidade inválida)"
    if quantidade > necessidade:
        return False, (
            f"REQ {nome_processo} {quantidade} -> ERRO "
            "(excede o máximo declarado)"
        )

    disponivel = calcular_disponivel(total, processos)  # Em t2.json, começa em 2

    # Regra ingênua do FCFS: se couber no saldo atual, entrega sem verificar segurança
    if quantidade <= disponivel:
        processo["possui"] += quantidade
        bloqueados.discard(nome_processo)  # Se estava bloqueado antes, volta a rodar

        # Se o processo atingiu seu máximo, conclui e libera todos os seus recursos
        if processo["possui"] == processo["maximo"]:
            liberado = processo["possui"]
            processo["possui"] = 0
            processo["maximo"] = 0
            processo["concluido"] = True
            return True, (
                f"REQ {nome_processo} {quantidade} -> CONCEDIDA (FCFS) | "
                f"Processo {nome_processo} concluiu e liberou {liberado} recursos "
                f"(disponível: {calcular_disponivel(total, processos)})"
            )

        # para fins didáticos: consulta 'esta_seguro' DEPOIS
        # da concessão para mostrar que o FCFS acabou de levar o sistema
        # para um ESTADO INSEGURO sem perceber.
        seguro, _ = esta_seguro(total, processos)
        alerta = (
            "sistema em ESTADO INSEGURO"
            if not seguro
            else "estado ainda seguro"
        )

        return True, (
            f"REQ {nome_processo} {quantidade} -> CONCEDIDA SEM VERIFICAÇÃO (FCFS) | "
            f"Disponível: {calcular_disponivel(total, processos)} ({alerta})"
        )

    # Saldo insuficiente -> o processo não recebe o recurso e fica bloqueado esperando
    bloqueados.add(nome_processo)
    return False, (
        f"REQ {nome_processo} {quantidade} -> BLOQUEADO (processo {nome_processo} "
        f"aguarda {quantidade}, mas disponível = {disponivel})"
    )


def verificar_deadlock_fcfs(
    total: int, processos: list[dict], bloqueados: set[str]
) -> tuple[bool, str]:
    """
    Diagnostica a situação final da Versão 2 (FCFS), diferenciando:
    1. DEADLOCK real: todos os processos ativos estão bloqueados esperando
       recursos e o saldo disponível não permite que nenhum deles conclua.
    2. ESTADO INSEGURO (ainda sem deadlock): nenhum processo consegue concluir
       com o saldo atual, mas nem todos estão bloqueados ainda — ilustra a
       pergunta teórica do trabalho ("Um estado inseguro leva sempre a deadlock?").
    3. Normal: ainda existem processos capazes de terminar.
    """
    ativos = [p for p in processos if p["maximo"] > 0]
    if not ativos:
        return False, "Todos os processos concluíram sem deadlock."

    disponivel = calcular_disponivel(total, processos)
    todos_bloqueados = all(p["nome"] in bloqueados for p in ativos)
    nenhum_pode_terminar = all(
        (p["maximo"] - p["possui"]) > disponivel for p in ativos
    )

    # Condição de deadlock: todos travados + ninguém consegue terminar para liberar recursos
    if todos_bloqueados and nenhum_pode_terminar:
        nomes = ", ".join(p["nome"] for p in ativos)
        return True, (
            f"DEADLOCK DETECTADO! Processos bloqueados permanentemente: [{nomes}]. "
            f"Disponível no cofre = {disponivel}, insuficiente para qualquer "
            "processo finalizar."
        )

    # Estado inseguro: ainda não travou todos, mas não há garantia de término
    if nenhum_pode_terminar:
        return False, (
            f"Sistema em ESTADO INSEGURO (disponível = {disponivel}); "
            "se os processos pedirem o restante de seus máximos, ocorrerá deadlock."
        )

    return False, "Sistema ainda possui processos capazes de concluir."


# =============================================================================
# 4. EXIBIÇÃO E ROTINAS DE DEMONSTRAÇÃO / TESTES
# =============================================================================

def exibir_resumo_estado(total: int, processos: list[dict]) -> None:
    """Imprime uma tabela organizada com Total, Disponível e situação de cada processo."""
    disponivel = calcular_disponivel(total, processos)
    separador = estilizar("-" * 64, AZUL)
    print(separador)
    print(estilizar(f"Total: {total} | Disponível: {disponivel}", NEGRITO))
    print(separador)
    print(
        estilizar(
            f"{'Processo':<10} | {'Possui':<8} | {'Máximo':<8} | "
            f"{'Necessidade':<12} | Situação",
            NEGRITO,
        )
    )
    print(separador)
    for p in processos:
        necessidade = p["maximo"] - p["possui"]
        situacao = "concluído" if p.get("concluido") else "ativo"
        print(
            f"{p['nome']:<10} | {p['possui']:<8} | {p['maximo']:<8} | "
            f"{necessidade:<12} | {situacao}"
        )
    print(separador)


def executar_requisicoes_fcfs(
    total: int, processos: list[dict], requisicoes: list[tuple[str, int]]
) -> set[str]:
    """Aplica uma lista de requisições em sequência usando a Versão 2 (FCFS)."""
    bloqueados: set[str] = set()
    for indice, (nome, quantidade) in enumerate(requisicoes, start=1):
        _, mensagem = solicitar_recurso_fcfs(
            total, processos, nome, quantidade, bloqueados
        )
        imprimir_requisicao(indice, len(requisicoes), mensagem)
    return bloqueados


def executar_comparacao() -> None:
    """
    Modo padrão da apresentação ao vivo (`python main.py`).

    Coloca as duas versões lado a lado sobre o MESMO estado inicial (t2.json) e
    a MESMA sequência de requisições (req_v2_deadlock.txt):
    - Versão 1 (Banqueiro): nega 'REQ B 1' porque levaria ao estado inseguro,
      mantém o sistema seguro e permite a conclusão dos processos sem bloqueio.
    - Versão 2 (FCFS):
        * [T6] Concede 'REQ B 1' sem checar segurança -> estado fica INSEGURO.
        * [T7] Ao processar os pedidos seguintes, todos os processos bloqueiam
          -> DEADLOCK DETECTADO.
    """
    requisicoes_t4 = ler_requisicoes(TESTES_DIR / "req_t4.txt")
    requisicoes_deadlock = ler_requisicoes(TESTES_DIR / "req_v2_deadlock.txt")

    imprimir_secao(
        "  COMPARAÇÃO: BANQUEIRO x First-Come, First-Served (FCFS)",
        "As duas versões partem do mesmo estado inicial.",
        caractere="━",
    )

    # --- Estado inicial comum (Slide 73 / T2: A 1/6, B 1/5, C 2/4, D 4/7; Disp = 2) ---
    total_base, processos_base = ler_input(TESTES_DIR / "t2.json")
    print(estilizar("Estado inicial comum (testes/t2.json):", NEGRITO))
    exibir_resumo_estado(total_base, processos_base)

    # --- Execução da Versão 1: Algoritmo do Banqueiro ---
    print()
    imprimir_secao(
        "ALGORITMO DO BANQUEIRO",
        "Nega o pedido que deixaria o estado inseguro; não bloqueia processos.",
        caractere="=",
    )
    total_v1, processos_v1 = ler_input(TESTES_DIR / "t2.json")
    print(estilizar("Requisições (testes/req_v2_deadlock.txt):", NEGRITO))
    concedidas_v1 = 0
    negadas_v1 = 0
    for indice, (nome, quantidade) in enumerate(requisicoes_deadlock, start=1):
        concedida, mensagem = solicitar_recurso(
            total_v1, processos_v1, nome, quantidade
        )
        if concedida:
            concedidas_v1 += 1
        else:
            negadas_v1 += 1
        imprimir_requisicao(indice, len(requisicoes_deadlock), mensagem)

    print()
    print(estilizar("Estado final:", NEGRITO))
    exibir_resumo_estado(total_v1, processos_v1)
    seguro_v1, sequencia_v1 = esta_seguro(total_v1, processos_v1)
    if seguro_v1:
        print(
            colorir_status(
                f"Diagnóstico (V1): estado SEGURO (sequência segura: "
                f"{formatar_sequencia(sequencia_v1)}); {concedidas_v1} concedida(s), "
                f"{negadas_v1} negada(s), nenhum processo bloqueado."
            )
        )
    else:
        print(
            colorir_status(
                f"Diagnóstico (V1): estado INSEGURO; {concedidas_v1} concedida(s), "
                f"{negadas_v1} negada(s)."
            )
        )

    # --- Execução da Versão 2: Alocação Ingênua / FCFS ---
    print()
    imprimir_secao(
        "alocação ingênua / FCFS",
        "Concede por ordem de chegada se houver saldo; não testa segurança.",
        caractere="━",
    )

    # T6: Mostra isoladamente o momento exato em que o sistema entra em ESTADO INSEGURO
    #     (o mesmo REQ B 1 que o Banqueiro negou no T4).
    print(estilizar("[T6] Estado do T2 + REQ B 1", NEGRITO, AMARELO))
    total_t6, processos_t6 = ler_input(TESTES_DIR / "t2.json")
    bloqueados_t6 = executar_requisicoes_fcfs(
        total_t6, processos_t6, requisicoes_t4
    )
    print()
    print(estilizar("Estado após o pedido:", NEGRITO))
    exibir_resumo_estado(total_t6, processos_t6)
    _, diagnostico_t6 = verificar_deadlock_fcfs(
        total_t6, processos_t6, bloqueados_t6
    )
    print(colorir_status(f"Diagnóstico (T6): {diagnostico_t6}"))

    # T7: Reinicia de t2.json e roda a sequência inteira até todos os processos travarem
    print()
    print(
        estilizar(
            "[T7] Sequência completa de testes/req_v2_deadlock.txt "
            "(reiniciando do estado inicial)",
            NEGRITO,
            VERMELHO,
        )
    )
    total_t7, processos_t7 = ler_input(TESTES_DIR / "t2.json")
    bloqueados_t7 = executar_requisicoes_fcfs(
        total_t7, processos_t7, requisicoes_deadlock
    )
    print()
    print(estilizar("Estado final:", NEGRITO))
    exibir_resumo_estado(total_t7, processos_t7)
    _, diagnostico_t7 = verificar_deadlock_fcfs(
        total_t7, processos_t7, bloqueados_t7
    )
    print(colorir_status(f"Diagnóstico (T7): {diagnostico_t7}"))

    # --- Quadro-resumo comparativo para encerrar a demonstração ---
    print()
    imprimir_secao(
        "  RESUMO DA COMPARAÇÃO",
        "Mesmo estado inicial e mesma sequência completa de requisições.",
        caractere="━",
    )
    print(
        colorir_status(
            f"Banqueiro : {concedidas_v1} concedida(s), {negadas_v1} negada(s), "
            "nenhum processo bloqueado -> sistema SEGURO."
        )
    )
    print(
        colorir_status(
            "FCFS      : 1 concessão deixou o estado INSEGURO, "
            f"{len(bloqueados_t7)} processo(s) bloqueado(s) -> "
            "DEADLOCK DETECTADO."
        )
    )
    print(
        estilizar(
            "Conclusão: o teste de segurança do Banqueiro evita o impasse que "
            "o FCFS não percebe.",
            NEGRITO,
        )
    )


def executar_testes() -> None:
    """
    Executa e valida automaticamente (via assert) os 5 casos de teste obrigatórios
    baseados no slide 73 da aula:

    - T1: A 0/6, B 0/5, C 0/4, D 0/7 (Disp = 10) -> Seguro
    - T2: A 1/6, B 1/5, C 2/4, D 4/7 (Disp = 2)  -> Seguro (sequência: C, D, A, B)
    - T3: A 1/6, B 2/5, C 2/4, D 4/7 (Disp = 1)  -> Inseguro
    - T4: Estado do T2 + requisição 'REQ B 1'    -> Negada (levaria ao estado T3)
    - T5: Estado do T2 + requisição 'REQ C 2'    -> Concedida (C conclui e libera recursos)
    """
    # T1: Cofre cheio (10 disponíveis), ninguém alocou nada -> garantidamente seguro
    total_t1, t1 = ler_input(TESTES_DIR / "t1.json")
    assert calcular_disponivel(total_t1, t1) == 10
    seguro, seq = esta_seguro(total_t1, t1)
    assert seguro is True
    print(estilizar("[T1] testes/t1.json | disponível = 10", NEGRITO, CIANO))
    print(colorir_status(f"     Seguro (sequência: {formatar_sequencia(seq)})"))

    # T2: Estado intermediário seguro; C precisa de 2 (== disponível) e inicia a cadeia
    total_t2, t2 = ler_input(TESTES_DIR / "t2.json")
    assert calcular_disponivel(total_t2, t2) == 2
    seguro, seq = esta_seguro(total_t2, t2)
    assert seguro is True and seq == ["C", "D", "A", "B"]
    print(estilizar("[T2] testes/t2.json | disponível = 2", NEGRITO, CIANO))
    print(colorir_status(f"     Seguro (sequência: {formatar_sequencia(seq)})"))

    # T3: Apenas 1 disponível, mas a menor necessidade entre os processos é 2 -> inseguro
    total_t3, t3 = ler_input(TESTES_DIR / "t3.json")
    assert calcular_disponivel(total_t3, t3) == 1
    seguro, _ = esta_seguro(total_t3, t3)
    assert seguro is False
    print(estilizar("[T3] testes/t3.json | disponível = 1", NEGRITO, CIANO))
    print(colorir_status("     Inseguro (não há sequência segura)"))

    # T4 e T5 partem do mesmo estado base (T2), usando deepcopy para não interferirem entre si
    print()
    print(estilizar("[T4/T5] Estado base: testes/t2.json", NEGRITO, CIANO))
    exibir_resumo_estado(total_t2, t2)

    # T4 (Estado do T2, requisição: B pede 1 -> levaria ao estado T3 -> deve ser NEGADA)
    print()
    print(estilizar("[T4] Requisição: REQ B 1", NEGRITO, CIANO))
    t4 = copy.deepcopy(t2)
    reqs_t4 = ler_requisicoes(TESTES_DIR / "req_t4.txt")
    for nome, qtd in reqs_t4:
        concedida, msg = solicitar_recurso(total_t2, t4, nome, qtd)
        assert concedida is False
        assert calcular_disponivel(total_t2, t4) == 2  # Garante que houve rollback (saldo intacto)
        print(colorir_status(f"     {msg}"))
    print("     Rollback confirmado: o estado permaneceu inalterado.")

    # T5 (Estado do T2, requisição: C pede 2 -> C completa 4/4, conclui e devolve recursos -> CONCEDIDA)
    print()
    print(estilizar("[T5] Requisição: REQ C 2", NEGRITO, CIANO))
    t5 = copy.deepcopy(t2)
    reqs_t5 = ler_requisicoes(TESTES_DIR / "req_t5.txt")
    for nome, qtd in reqs_t5:
        concedida, msg = solicitar_recurso(total_t2, t5, nome, qtd)
        assert concedida is True
        assert "C, D, A, B" in msg
        print(colorir_status(f"     {msg}"))
    print("     Estado após a concessão:")
    exibir_resumo_estado(total_t2, t5)

    print()
    print(
        estilizar("Todos os testes T1 a T5 passaram com sucesso!", NEGRITO, VERDE)
    )


# =============================================================================
# 5. PONTO DE ENTRADA (INTERFACE DE LINHA DE COMANDO)
# =============================================================================

def main() -> None:
    """Configura os argumentos de linha de comando e escolhe o modo de execução."""
    parser = argparse.ArgumentParser(
        description="Simulador do Algoritmo do Banqueiro (Trabalho 3)."
    )
    parser.add_argument(
        "-t",
        "--testes",
        action="store_true",
        help="executa apenas os testes obrigatórios T1 a T5",
    )
    args = parser.parse_args()

    # Se o usuário passou --testes (ou -t), roda apenas a bateria obrigatória T1–T5
    if args.testes:
        imprimir_secao(
            "  ALGORITMO DO BANQUEIRO - TESTES T1 A T5",
            "Executa somente os casos de teste obrigatórios.",
            caractere="━",
        )
        executar_testes()
        return

    # Caso contrário, roda a demonstração comparativa completa (Banqueiro x FCFS)
    executar_comparacao()


if __name__ == "__main__":
    main()