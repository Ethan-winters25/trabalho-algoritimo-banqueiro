import json
import copy
from pathlib import Path

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
    # TODO: Implementar cálculo de recursos disponíveis
    pass


def validar_estado(total: int, processos: list[dict]) -> None:
    # TODO: Implementar validação do estado dos processos e recursos
    pass


def esta_seguro(total: int, processos: list[dict]) -> tuple[bool, list[str]]:
    # TODO: Implementar verificação de estado seguro (Algoritmo do Banqueiro)
    pass


def solicitar_recurso(
    total: int, processos: list[dict], nome_processo: str, quantidade: int
) -> tuple[bool, str]:
    # TODO: Implementar processamento de solicitação de recurso
    pass


def executar_arquivos(caminho_json: Path, caminho_req: Path) -> None:
    # TODO: Implementar execução a partir dos arquivos de entrada e requisições
    pass


def executar_testes() -> None:
    """Executa os casos de teste obrigatórios T1 a T5."""
    # T1
    total_t1, t1 = ler_input(TESTES_DIR / "t1.json")
    assert calcular_disponivel(total_t1, t1) == 10
    seguro, seq = esta_seguro(total_t1, t1)
    assert seguro is True
    print(f"T1: Seguro (sequência: {', '.join(seq)})")

    # T2
    total_t2, t2 = ler_input(TESTES_DIR / "t2.json")
    assert calcular_disponivel(total_t2, t2) == 2
    seguro, seq = esta_seguro(total_t2, t2)
    assert seguro is True and seq == ["C", "D", "A", "B"]
    print(f"T2: Seguro (sequência: {', '.join(seq)})")

    # T3
    total_t3, t3 = ler_input(TESTES_DIR / "t3.json")
    assert calcular_disponivel(total_t3, t3) == 1
    seguro, _ = esta_seguro(total_t3, t3)
    assert seguro is False
    print("T3: Inseguro")

    # T4 (Estado do T2, requisição: B pede 1)
    t4 = copy.deepcopy(t2)
    reqs_t4 = ler_requisicoes(TESTES_DIR / "req_t4.txt")
    for nome, qtd in reqs_t4:
        concedida, msg = solicitar_recurso(total_t2, t4, nome, qtd)
        assert concedida is False
        assert calcular_disponivel(total_t2, t4) == 2  # Garante que houve rollback
        print(f"T4: REQ {nome} {qtd} -> {msg}")

    # T5 (Estado do T2, requisição: C pede 2)
    t5 = copy.deepcopy(t2)
    reqs_t5 = ler_requisicoes(TESTES_DIR / "req_t5.txt")
    for nome, qtd in reqs_t5:
        concedida, msg = solicitar_recurso(total_t2, t5, nome, qtd)
        assert concedida is True
        assert "C, D, A, B" in msg
        print(f"T5: REQ {nome} {qtd} -> {msg}")

    print("\nTodos os testes T1 a T5 passaram com sucesso!")


def main():
    total, processos = ler_input(TESTES_DIR / "t2.json")
    reqs = ler_requisicoes(TESTES_DIR / "req_t4.txt")

    print(total)      # 10
    print(processos)  # Lista de processos

    for nome, qtd in reqs:
        #_, mensagem = solicitar_recurso(total, processos, nome, qtd)
        # TODO: solicitar recurso impl
        print(f"REQ {nome} {qtd}")


if __name__ == "__main__":
    main()
