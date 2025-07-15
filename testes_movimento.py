# testes_movimento.py

from logica_movimento import eh_movimento_valido
from utils import converter_notacao_para_indices
from tabuleiro import criar_tabuleiro_inicial


def testar_movimentos_peao():
    print("--- INICIANDO TESTES DO PEÃO ---")
    tabuleiro_inicial = criar_tabuleiro_inicial()
    assert eh_movimento_valido(tabuleiro_inicial, converter_notacao_para_indices('e2'),
                               converter_notacao_para_indices('e4'),
                               'branco') == True, "Falha: Peão branco mover 2 casas"
    assert eh_movimento_valido(tabuleiro_inicial, converter_notacao_para_indices('e2'),
                               converter_notacao_para_indices('d3'),
                               'branco') == False, "Falha: Peão mover na diagonal sem captura"
    print("✅ Testes básicos do Peão passaram com sucesso!")


def testar_movimentos_torre():
    print("\n--- INICIANDO TESTES DA TORRE ---")
    tabuleiro_teste = [
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', 'p', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', 'R', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', 'P', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
    ]
    inicio = converter_notacao_para_indices('d4')
    assert eh_movimento_valido(tabuleiro_teste, inicio, converter_notacao_para_indices('d1'),
                               'branco') == False, "Falha: Torre pular peça inimiga"
    assert eh_movimento_valido(tabuleiro_teste, inicio, converter_notacao_para_indices('h4'),
                               'branco') == False, "Falha: Torre pular peça amiga"
    print("✅ Todos os testes da Torre passaram com sucesso!")


def testar_movimentos_bispo():
    print("\n--- INICIANDO TESTES DO BISPO ---")
    tabuleiro_bloqueio = [
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', 'p', '.', '.', '.', '.', '.'],
        ['.', '.', '.', 'B', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', 'P', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
    ]
    inicio = converter_notacao_para_indices('d5')
    assert eh_movimento_valido(tabuleiro_bloqueio, inicio, converter_notacao_para_indices('a8'),
                               'branco') == False, "Falha: Bispo pular peça inimiga"
    assert eh_movimento_valido(tabuleiro_bloqueio, inicio, converter_notacao_para_indices('h1'),
                               'branco') == False, "Falha: Bispo pular peça amiga"
    print("✅ Todos os testes do Bispo passaram com sucesso!")


def testar_movimentos_cavalo():
    print("\n--- INICIANDO TESTES DO CAVALO ---")

    tabuleiro_teste = [
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', 'N', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.']
    ]
    inicio = converter_notacao_para_indices('e4')  # (4, 4)

    print("Testando movimentos válidos...")
    # Testar um movimento válido
    assert eh_movimento_valido(tabuleiro_teste, inicio, converter_notacao_para_indices('d6'),
                               'branco') == True, "Falha: Mover para d6"
    assert eh_movimento_valido(tabuleiro_teste, inicio, converter_notacao_para_indices('f6'),
                               'branco') == True, "Falha: Mover para f6"

    print("Testando movimentos inválidos...")
    # Testar um movimento inválido
    assert eh_movimento_valido(tabuleiro_teste, inicio, converter_notacao_para_indices('e5'),
                               'branco') == False, "Falha: Mover em linha reta"

    print("✅ Todos os testes do Cavalo passaram com sucesso!")


# ==============================================================================
# FUNÇÃO DE TESTE PARA A RAINHA
# ==============================================================================
def testar_movimentos_rainha():
    print("\n--- INICIANDO TESTES DA RAINHA ---")

    # CENÁRIO 1: MOVIMENTOS VÁLIDOS EM CAMINHO LIVRE
    tabuleiro_livre = [
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', 'Q', '.', '.', '.', '.'],  # Rainha branca em d5
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.']
    ]
    inicio = converter_notacao_para_indices('d5')

    print("Testando movimentos válidos em caminho livre...")
    assert eh_movimento_valido(tabuleiro_livre, inicio, converter_notacao_para_indices('d8'),
                               'branco') == True, "Falha: Mover para cima (Torre)"
    assert eh_movimento_valido(tabuleiro_livre, inicio, converter_notacao_para_indices('a5'),
                               'branco') == True, "Falha: Mover para esquerda (Torre)"
    assert eh_movimento_valido(tabuleiro_livre, inicio, converter_notacao_para_indices('a8'),
                               'branco') == True, "Falha: Mover para cima-esquerda (Bispo)"
    assert eh_movimento_valido(tabuleiro_livre, inicio, converter_notacao_para_indices('h1'),
                               'branco') == True, "Falha: Mover para baixo-direita (Bispo)"

    # CENÁRIO 2: CAPTURAS E BLOQUEIOS
    tabuleiro_pecas = [
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', 'p', '.', '.', '.', '.', '.'],  # Peão inimigo em c6
        ['.', '.', '.', 'Q', '.', 'r', '.', '.'],  # Rainha em d5, TORRE INIMIGA EM F5
        ['.', '.', '.', 'P', '.', '.', '.', '.'],  # Peão amigo em d4
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.']
    ]

    print("Testando capturas e bloqueios...")
    # Capturas válidas
    assert eh_movimento_valido(tabuleiro_pecas, inicio, converter_notacao_para_indices('c6'),
                               'branco') == True, "Falha: Capturar na diagonal"
    assert eh_movimento_valido(tabuleiro_pecas, inicio, converter_notacao_para_indices('f5'),
                               'branco') == True, "Falha: Capturar na horizontal"

    # Movimentos bloqueados
    # Tenta pular o peão amigo em d4 para chegar em d2
    assert eh_movimento_valido(tabuleiro_pecas, inicio, converter_notacao_para_indices('d2'),
                               'branco') == False, "Falha: Pular peça amiga (vertical)"
    # Tenta pular a torre inimiga em f5 para chegar em h5
    assert eh_movimento_valido(tabuleiro_pecas, inicio, converter_notacao_para_indices('h5'),
                               'branco') == False, "Falha: Pular peça inimiga (horizontal)"
    # Tenta pular o peão inimigo em c6 para chegar em a8
    assert eh_movimento_valido(tabuleiro_pecas, inicio, converter_notacao_para_indices('a8'),
                               'branco') == False, "Falha: Pular peça inimiga (diagonal)"

    # Cenário 3: Movimento inválido (como Cavalo)
    print("Testando movimentos tipo cavalo...")
    assert eh_movimento_valido(tabuleiro_livre, inicio, converter_notacao_para_indices('e7'),
                               'branco') == False, "Falha: Mover como cavalo"

    print("✅ Todos os testes da Rainha passaram com sucesso!")


# ==============================================================================
# FUNÇÃO DE TESTE PARA O REI
# ==============================================================================
def testar_movimentos_rei():
    print("\n--- INICIANDO TESTES DO REI ---")

    tabuleiro_teste = [
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', 'K', 'P', '.', '.'],  # Rei em d5, Peão amigo em e5
        ['.', '.', '.', 'p', '.', '.', '.', '.'],  # peão inimigo em d4
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.']
    ]
    inicio = converter_notacao_para_indices('d5')  # (3, 3)

    # Cenário 1: Movimentos válidos para casas vazias
    print("Testando movimentos válidos para casas vazias...")
    # As 8 casas ao redor
    assert eh_movimento_valido(tabuleiro_teste, inicio, converter_notacao_para_indices('c6'),
                               'branco') == True, "Falha: Mover para c6"
    assert eh_movimento_valido(tabuleiro_teste, inicio, converter_notacao_para_indices('d6'),
                               'branco') == True, "Falha: Mover para d6"
    assert eh_movimento_valido(tabuleiro_teste, inicio, converter_notacao_para_indices('e6'),
                               'branco') == True, "Falha: Mover para e6"
    assert eh_movimento_valido(tabuleiro_teste, inicio, converter_notacao_para_indices('c5'),
                               'branco') == True, "Falha: Mover para c5"
    assert eh_movimento_valido(tabuleiro_teste, inicio, converter_notacao_para_indices('c4'),
                               'branco') == True, "Falha: Mover para c4"
    assert eh_movimento_valido(tabuleiro_teste, inicio, converter_notacao_para_indices('e4'),
                               'branco') == True, "Falha: Mover para e4"

    # Cenário 2: Captura e bloqueio
    print("Testando captura e bloqueio...")
    # Captura válida de peça inimiga
    assert eh_movimento_valido(tabuleiro_teste, inicio, converter_notacao_para_indices('d4'),
                               'branco') == True, "Falha: Capturar peça inimiga em d4"
    # Movimento bloqueado por peça amiga
    assert eh_movimento_valido(tabuleiro_teste, inicio, converter_notacao_para_indices('e5'),
                               'branco') == False, "Falha: Mover para casa com peça amiga em e5"

    # Cenário 3: Movimentos inválidos (distância > 1)
    print("Testando movimentos longos inválidos...")
    assert eh_movimento_valido(tabuleiro_teste, inicio, converter_notacao_para_indices('d7'),
                               'branco') == False, "Falha: Mover 2 casas na vertical"
    assert eh_movimento_valido(tabuleiro_teste, inicio, converter_notacao_para_indices('f7'),
                               'branco') == False, "Falha: Mover 2 casas na diagonal"
    assert eh_movimento_valido(tabuleiro_teste, inicio, converter_notacao_para_indices('b5'),
                               'branco') == False, "Falha: Mover 2 casas na horizontal"
    assert eh_movimento_valido(tabuleiro_teste, inicio, converter_notacao_para_indices('d5'),
                               'branco') == False, "Falha: Mover para a mesma casa"

    print("✅ Todos os testes do Rei passaram com sucesso!")


if __name__ == "__main__":
    testar_movimentos_peao()
    testar_movimentos_torre()
    testar_movimentos_bispo()
    testar_movimentos_cavalo()
    testar_movimentos_rainha()
    testar_movimentos_rei()