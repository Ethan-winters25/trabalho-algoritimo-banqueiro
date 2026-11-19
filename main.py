import json
from pathlib import Path

def ler_input(caminho: Path):
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


def main():
    total, processos = ler_input(Path("entradas.json"))
    reqs = ler_requisicoes(Path("requisicoes.txt"))

    print(total)      # 10
    print(processos)  # Lista de processos
    
    for nome, qtd in reqs:
        #_, mensagem = solicitar_recurso(total, processos, nome, qtd)
        # TODO: solicitar recurso impl
        print(f"REQ {nome} {qtd}")


if __name__ == "__main__":
    main()
