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

import argparse
import copy
import json
from pathlib import Path

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

TESTES_DIR = Path(__file__).resolve().parent / "testes"


def ler_input(caminho: Path) -> tuple[int, list[dict]]:
    with open(caminho, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    total = dados["total"]
    processos = dados["processos"]

    return total, processos
    
def ler_requisicoes(caminho: Path) -> list[tuple[str, int]]:
    requisicoes: list[tuple[str, int]] = []
    with open(caminho, "r", encoding="utf-8") as f:
        for num_linha, linha in enumerate(f, start=1):
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue

            partes = linha.split()
            if len(partes) != 3 or partes[0].upper() != "REQ":
                raise ValueError(
                    f"Linha {num_linha} inválida: '{linha}'. Formato esperado: REQ <PROCESSO> <QTD>"
                )

            nome = partes[1]
            qtd = int(partes[2])
            requisicoes.append((nome, qtd))
    return requisicoes


def calcular_disponivel(total: int, processos: list[dict]) -> int:
    total_possuido = sum(p["possui"] for p in processos)
    return total - total_possuido


def formatar_sequencia(sequencia: list[str]) -> str:
    """Formata a sequência segura para exibição."""
    return ", ".join(sequencia) if sequencia else "nenhum processo pendente"


def imprimir_requisicao(indice: int, total: int, mensagem: str) -> None:
    """Imprime uma requisição numerada, com o status destacado."""
    etiqueta = estilizar(f"  [{indice}/{total}]", NEGRITO, CIANO)
    print(f"{etiqueta} {colorir_status(mensagem)}")


def validar_estado(total: int, processos: list[dict]) -> None:
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


def esta_seguro(total: int, processos: list[dict]) -> tuple[bool, list[str]]:
    work = calcular_disponivel(total, processos)
    if work < 0:
        return False, []

    # Processos já concluídos não precisam mais entrar na sequência segura.
    ativos = [p for p in processos if not p.get("concluido")]
    n = len(ativos)
    finalizado = [False] * n
    sequencia: list[str] = []

    while len(sequencia) < n:
        progrediu = False
        for i, p in enumerate(ativos):
            necessidade = p["maximo"] - p["possui"]
           
            if not finalizado[i] and necessidade <= work:
               
                work += p["possui"]
                finalizado[i] = True
                sequencia.append(p["nome"])
                progrediu = True

       
        if not progrediu:
            return False, []

    return True, sequencia


def solicitar_recurso(
    total: int, processos: list[dict], nome_processo: str, quantidade: int
) -> tuple[bool, str]:
    """
    Versão 1 - Algoritmo do Banqueiro (evita impasses).

    Valida o pedido e simula a concessão em uma cópia do estado. A alocação só
    é efetivada se o estado resultante permanecer seguro; caso contrário, o
    pedido é negado e o estado original permanece intacto (rollback).
    Quando o processo atinge seu máximo, ele conclui e devolve os recursos.
    """
    processo = next((p for p in processos if p["nome"] == nome_processo), None)
    if processo is None:
        return False, (
            f"REQ {nome_processo} {quantidade} -> NEGADA "
            f"(processo '{nome_processo}' não existe)"
        )

    necessidade = processo["maximo"] - processo["possui"]

    if quantidade <= 0:
        return False, (
            f"REQ {nome_processo} {quantidade} -> NEGADA (quantidade inválida)"
        )
    if quantidade > necessidade:
        return False, (
            f"REQ {nome_processo} {quantidade} -> NEGADA "
            "(excede o máximo declarado pelo processo)"
        )

    disponivel = calcular_disponivel(total, processos)
    if quantidade > disponivel:
        return False, (
            f"REQ {nome_processo} {quantidade} -> NEGADA "
            f"(recursos disponíveis insuficientes: {disponivel})"
        )

    # Simula a concessão em uma cópia
    # o estado real só muda se o resultado continuar seguro (prevenção de impasses).
    estado_simulado = copy.deepcopy(processos)
    for p in estado_simulado:
        if p["nome"] == nome_processo:
            p["possui"] += quantidade
            break

    seguro, sequencia = esta_seguro(total, estado_simulado)
    if not seguro:
        return False, (
            f"REQ {nome_processo} {quantidade} -> NEGADA (estado resultante inseguro)"
        )

    processo["possui"] += quantidade
    seq_str = formatar_sequencia(sequencia)

    # Se o processo atingiu o máximo, conclui e devolve todos os recursos.
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
    Executa a Versão 1 a partir dos arquivos de estado e de requisições.

    Lê o JSON, valida o estado inicial, exibe a tabela de recursos e processa
    cada linha `REQ <processo> <quantidade>` do arquivo de requisições,
    imprimindo o resultado de cada pedido e o estado final do sistema.
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


def solicitar_recurso_fcfs(
    total: int,
    processos: list[dict],
    nome_processo: str,
    quantidade: int,
    bloqueados: set[str],
) -> tuple[bool, str]:
    """
    Versão 2 - Alocação Ingênua / FCFS (First-Come, First-Served).

    Atende imediatamente qualquer pedido que caiba no saldo disponível no
    instante, sem verificar se o estado resultante é seguro. Se faltar recurso,
    o processo fica bloqueado aguardando liberação. É justamente essa ausência
    de verificação que permite ao sistema entrar em estado inseguro e evoluir
    para um deadlock.
    """
    processo = next((p for p in processos if p["nome"] == nome_processo), None)
    if processo is None:
        return False, (
            f"REQ {nome_processo} {quantidade} -> ERRO "
            f"(processo '{nome_processo}' não existe)"
        )

    necessidade = processo["maximo"] - processo["possui"]

    if quantidade <= 0:
        return False, f"REQ {nome_processo} {quantidade} -> ERRO (quantidade inválida)"
    if quantidade > necessidade:
        return False, (
            f"REQ {nome_processo} {quantidade} -> ERRO "
            "(excede o máximo declarado)"
        )

    disponivel = calcular_disponivel(total, processos)

    if quantidade <= disponivel:
        processo["possui"] += quantidade
        bloqueados.discard(nome_processo)

        # Se o processo atingiu seu máximo, conclui e devolve todos os recursos.
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

    bloqueados.add(nome_processo)
    return False, (
        f"REQ {nome_processo} {quantidade} -> BLOQUEADO (processo {nome_processo} "
        f"aguarda {quantidade}, mas disponível = {disponivel})"
    )


def verificar_deadlock_fcfs(
    total: int, processos: list[dict], bloqueados: set[str]
) -> tuple[bool, str]:
    """
    Verifica se a Versão 2 chegou a um deadlock: todos os processos ativos
    ficaram bloqueados e nenhum consegue atingir seu máximo com o saldo atual.
    """
    ativos = [p for p in processos if p["maximo"] > 0]
    if not ativos:
        return False, "Todos os processos concluíram sem deadlock."

    disponivel = calcular_disponivel(total, processos)
    todos_bloqueados = all(p["nome"] in bloqueados for p in ativos)
    nenhum_pode_terminar = all(
        (p["maximo"] - p["possui"]) > disponivel for p in ativos
    )

    if todos_bloqueados and nenhum_pode_terminar:
        nomes = ", ".join(p["nome"] for p in ativos)
        return True, (
            f"DEADLOCK DETECTADO! Processos bloqueados permanentemente: [{nomes}]. "
            f"Disponível no cofre = {disponivel}, insuficiente para qualquer "
            "processo finalizar."
        )
    if nenhum_pode_terminar:
        return False, (
            f"Sistema em ESTADO INSEGURO (disponível = {disponivel}); "
            "se os processos pedirem o restante de seus máximos, ocorrerá deadlock."
        )
    return False, "Sistema ainda possui processos capazes de concluir."


def exibir_resumo_estado(total: int, processos: list[dict]) -> None:
    """Imprime uma tabela com o estado atual do sistema."""
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
    """Processa uma sequência de requisições na Versão 2 e retorna os bloqueados."""
    bloqueados: set[str] = set()
    for indice, (nome, quantidade) in enumerate(requisicoes, start=1):
        _, mensagem = solicitar_recurso_fcfs(
            total, processos, nome, quantidade, bloqueados
        )
        imprimir_requisicao(indice, len(requisicoes), mensagem)
    return bloqueados


def executar_comparacao() -> None:
    """
    Compara as duas versões sobre o mesmo estado inicial (t2.json) e a mesma
    sequência de requisições (req_v2_deadlock.txt).

    A Versão 1 nega o pedido que levaria ao estado inseguro e preserva o
    sistema. A Versão 2 (FCFS) concede o mesmo pedido sem verificação, reduz o
    disponível e termina em deadlock.
    """
    requisicoes_t4 = ler_requisicoes(TESTES_DIR / "req_t4.txt")
    requisicoes_deadlock = ler_requisicoes(TESTES_DIR / "req_v2_deadlock.txt")

    imprimir_secao(
        "  COMPARAÇÃO: BANQUEIRO x FCFS",
        "As duas versões partem do mesmo estado inicial.",
        caractere="━",
    )

    # Estado inicial comum ---------------------------------------------------
    total_base, processos_base = ler_input(TESTES_DIR / "t2.json")
    print(estilizar("Estado inicial comum (testes/t2.json):", NEGRITO))
    exibir_resumo_estado(total_base, processos_base)

    # Versão 1 ---------------------------------------------------------------
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

    # Versão 2 ---------------------------------------------------------------
    print()
    imprimir_secao(
        "alocação ingênua / FCFS",
        "Concede por ordem de chegada se houver saldo; não testa segurança.",
        caractere="━",
    )

    # T6: o mesmo pedido do T4, agora concedido sem verificação de segurança.
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

    # T7: sequência completa que leva todos os processos ao deadlock.
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

    # Resumo -----------------------------------------------------------------
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
    """Executa os casos de teste obrigatórios T1 a T5."""
    # T1
    total_t1, t1 = ler_input(TESTES_DIR / "t1.json")
    assert calcular_disponivel(total_t1, t1) == 10
    seguro, seq = esta_seguro(total_t1, t1)
    assert seguro is True
    print(estilizar("[T1] testes/t1.json | disponível = 10", NEGRITO, CIANO))
    print(colorir_status(f"     Seguro (sequência: {formatar_sequencia(seq)})"))

    # T2
    total_t2, t2 = ler_input(TESTES_DIR / "t2.json")
    assert calcular_disponivel(total_t2, t2) == 2
    seguro, seq = esta_seguro(total_t2, t2)
    assert seguro is True and seq == ["C", "D", "A", "B"]
    print(estilizar("[T2] testes/t2.json | disponível = 2", NEGRITO, CIANO))
    print(colorir_status(f"     Seguro (sequência: {formatar_sequencia(seq)})"))

    # T3
    total_t3, t3 = ler_input(TESTES_DIR / "t3.json")
    assert calcular_disponivel(total_t3, t3) == 1
    seguro, _ = esta_seguro(total_t3, t3)
    assert seguro is False
    print(estilizar("[T3] testes/t3.json | disponível = 1", NEGRITO, CIANO))
    print(colorir_status("     Inseguro (não há sequência segura)"))

    # T4 e T5 partem do mesmo estado base.
    print()
    print(estilizar("[T4/T5] Estado base: testes/t2.json", NEGRITO, CIANO))
    exibir_resumo_estado(total_t2, t2)

    # T4 (Estado do T2, requisição: B pede 1)
    print()
    print(estilizar("[T4] Requisição: REQ B 1", NEGRITO, CIANO))
    t4 = copy.deepcopy(t2)
    reqs_t4 = ler_requisicoes(TESTES_DIR / "req_t4.txt")
    for nome, qtd in reqs_t4:
        concedida, msg = solicitar_recurso(total_t2, t4, nome, qtd)
        assert concedida is False
        assert calcular_disponivel(total_t2, t4) == 2  # Garante que houve rollback
        print(colorir_status(f"     {msg}"))
    print("     Rollback confirmado: o estado permaneceu inalterado.")

    # T5 (Estado do T2, requisição: C pede 2)
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


def main() -> None:
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

    if args.testes:
        imprimir_secao(
            "  ALGORITMO DO BANQUEIRO - TESTES T1 A T5",
            "Executa somente os casos de teste obrigatórios.",
            caractere="━",
        )
        executar_testes()
        return

    executar_comparacao()


if __name__ == "__main__":
    main()
