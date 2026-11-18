import json

def ler_input(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    total = dados["total"]
    processos = dados["processos"]

    return total, processos


def main():
    total, processos = ler_input("entradas.json")

    print(total)      # 10
    print(processos)  # Lista de processos


if __name__ == "__main__":
    main()
# TODO: Ler e parsear entradas.json

if __name__ == "__main__":
    main()
