# tabuleiro.py

def criar_tabuleiro_inicial():
    """Cria e retorna a posição inicial do tabuleiro como uma lista de listas."""
    return [
        ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],  # Rainha ('q') em d8, Rei ('k') em e8
        ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
        ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']   # Rainha ('Q') em d1, Rei ('K') em e1
    ]

def exibir_tabuleiro(tabuleiro):
    """Exibe o estado atual do tabuleiro no console com coordenadas."""
    print("\n  a b c d e f g h")
    print(" +-----------------+")
    for i, linha in enumerate(tabuleiro):
        print(f"{8 - i}| {' '.join(linha)} |{8 - i}")
    print(" +-----------------+")
    print("  a b c d e f g h\n")