"""
Estilização de saída para o terminal (cores ANSI e negrito).

As funções deste módulo mantêm a lógica do simulador independente da
apresentação: as mensagens continuam sendo textos simples e só recebem cor na
hora de imprimir. Quando o terminal não suporta ANSI, tudo é impresso sem
códigos de escape.

Variáveis de ambiente:
    NO_COLOR     desativa as cores (qualquer valor não vazio).
    FORCE_COLOR  força as cores mesmo quando a saída não é um terminal.
"""

import os
import re
import sys

# ---------------------------------------------------------------------------
# Códigos ANSI
# ---------------------------------------------------------------------------
RESET = "\033[0m"
NEGRITO = "\033[1m"
VERMELHO = "\033[31m"
VERDE = "\033[32m"
AMARELO = "\033[33m"
AZUL = "\033[34m"
CIANO = "\033[36m"


def _habilitar_ansi_windows() -> bool:
    """Ativa o processamento de sequências ANSI no console do Windows."""
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        modo = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(modo)):
            return False
        enable_vt = 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        return bool(kernel32.SetConsoleMode(handle, modo.value | enable_vt))
    except (AttributeError, OSError, ValueError):
        return False


def _terminal_suporta_cor() -> bool:
    """Decide se o terminal atual aceita sequências ANSI."""
    if os.environ.get("NO_COLOR"):
        return False
    force_color = os.environ.get("FORCE_COLOR")
    if force_color and force_color != "0":
        if os.name == "nt":
            _habilitar_ansi_windows()
        return True
    if not sys.stdout.isatty():
        return False
    if os.name == "nt":
        return _habilitar_ansi_windows()
    return True


USAR_COR = _terminal_suporta_cor()


def estilizar(texto: str, *estilos: str) -> str:
    """Aplica códigos ANSI ao texto quando o terminal suporta cor."""
    if not USAR_COR or not estilos:
        return texto
    return f"{''.join(estilos)}{texto}{RESET}"


# Palavras-chave destacadas nas mensagens de requisição/diagnóstico.
_STATUS_COLORIDO = re.compile(
    r"(DEADLOCK DETECTADO|ESTADO INSEGURO|ATENÇÃO|CONCEDIDA|NEGADA|"
    r"BLOQUEADO|ERRO|INSEGURO|SEGURO|Seguro|Inseguro|inseguro|seguro)"
)

_CORES_STATUS = {
    "CONCEDIDA": VERDE,
    "SEGURO": VERDE,
    "NEGADA": VERMELHO,
    "ERRO": VERMELHO,
    "DEADLOCK DETECTADO": VERMELHO,
    "INSEGURO": VERMELHO,
    "ESTADO INSEGURO": VERMELHO,
    "BLOQUEADO": AMARELO,
    "ATENÇÃO": AMARELO,
}


def colorir_status(texto: str) -> str:
    """Destaca em negrito e cor as palavras-chave de status da simulação."""
    if not USAR_COR:
        return texto

    def destacar(match: re.Match) -> str:
        palavra = match.group(0)
        cor = _CORES_STATUS[palavra.upper()]
        return estilizar(palavra, NEGRITO, cor)

    return _STATUS_COLORIDO.sub(destacar, texto)


def imprimir_secao(titulo: str, subtitulo: str = "", caractere: str = "=") -> None:
    """Imprime um cabeçalho de seção em negrito e ciano."""
    linha = estilizar(caractere * 64, NEGRITO, CIANO)
    print(linha)
    print(estilizar(titulo, NEGRITO, CIANO))
    if subtitulo:
        print(estilizar(subtitulo, NEGRITO))
    print(linha)
