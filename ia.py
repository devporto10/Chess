# ia.py

import random
import copy
import time
from regras_jogo import gerar_todos_movimentos_legais, verificar_fim_de_jogo, gerar_hash_posicao, encontrar_posicao_rei

PONTUACAO_PECAS = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
PST_PEAO = [[0, 0, 0, 0, 0, 0, 0, 0], [50, 50, 50, 50, 50, 50, 50, 50], [10, 10, 20, 30, 30, 20, 10, 10],
            [5, 5, 10, 25, 25, 10, 5, 5], [0, 0, 0, 20, 20, 0, 0, 0], [5, -5, -10, 0, 0, -10, -5, 5],
            [5, 10, 10, -20, -20, 10, 10, 5], [0, 0, 0, 0, 0, 0, 0, 0]]
PST_CAVALO = [[-50, -40, -30, -30, -30, -30, -40, -50], [-40, -20, 0, 5, 5, 0, -20, -40],
              [-30, 5, 10, 15, 15, 10, 5, -30], [-30, 0, 15, 20, 20, 15, 0, -30], [-30, 5, 15, 20, 20, 15, 5, -30],
              [-30, 0, 10, 15, 15, 10, 0, -30], [-40, -20, 0, 0, 0, 0, -20, -40],
              [-50, -40, -30, -30, -30, -30, -40, -50]]
PST_BISPO = [[-20, -10, -10, -10, -10, -10, -10, -20], [-10, 0, 0, 0, 0, 0, 0, -10], [-10, 0, 5, 10, 10, 5, 0, -10],
             [-10, 5, 5, 10, 10, 5, 5, -10], [-10, 0, 10, 10, 10, 10, 0, -10], [-10, 10, 10, 10, 10, 10, 10, -10],
             [-10, 5, 0, 0, 0, 0, 5, -10], [-20, -10, -10, -10, -10, -10, -10, -20]]
PST_TORRE = [[0, 0, 0, 5, 5, 0, 0, 0], [-5, 0, 0, 0, 0, 0, 0, -5], [-5, 0, 0, 0, 0, 0, 0, -5],
             [-5, 0, 0, 0, 0, 0, 0, -5], [-5, 0, 0, 0, 0, 0, 0, -5], [-5, 0, 0, 0, 0, 0, 0, -5],
             [5, 10, 10, 10, 10, 10, 10, 5], [0, 0, 0, 0, 0, 0, 0, 0]]
PST_RAINHA = [[-20, -10, -10, -5, -5, -10, -10, -20], [-10, 0, 5, 0, 0, 0, 0, -10], [-10, 5, 5, 5, 5, 5, 0, -10],
              [0, 0, 5, 5, 5, 5, 0, -5], [-5, 0, 5, 5, 5, 5, 0, -5], [-10, 0, 5, 5, 5, 5, 0, -10],
              [-10, 0, 0, 0, 0, 0, 0, -10], [-20, -10, -10, -5, -5, -10, -10, -20]]
TABELAS_POSICAO = {'P': PST_PEAO, 'N': PST_CAVALO, 'B': PST_BISPO, 'R': PST_TORRE, 'Q': PST_RAINHA}


# --- Funções de Avaliação Específicas ---

def avaliar_seguranca_rei(tabuleiro, cor_rei):
    pos_rei = encontrar_posicao_rei(tabuleiro, cor_rei)
    if not pos_rei: return 0
    r_rei, c_rei = pos_rei;
    pontuacao_seguranca = 0
    peao_aliado = 'P' if cor_rei == 'branco' else 'p'
    if (cor_rei == 'branco' and r_rei == 7 and c_rei in [2, 6]) or \
            (cor_rei == 'preto' and r_rei == 0 and c_rei in [2, 6]):
        pontuacao_seguranca += 50
    direcao = -1 if cor_rei == 'branco' else 1
    for dc in [-1, 0, 1]:
        c = c_rei + dc
        if 0 <= c <= 7:
            if 0 <= r_rei + direcao <= 7:
                if tabuleiro[r_rei + direcao][c] != peao_aliado: pontuacao_seguranca -= 15
            else:
                pontuacao_seguranca -= 10
            if all(tabuleiro[r][c] != peao_aliado for r in range(8)): pontuacao_seguranca -= 25
    return pontuacao_seguranca


def avaliar_estrutura_peoes(tabuleiro, cor):
    pontuacao = 0;
    peao_aliado = 'P' if cor == 'branco' else 'p'
    posicoes_peoes = [(r, c) for r in range(8) for c in range(8) if tabuleiro[r][c] == peao_aliado]
    colunas_com_peoes = {c for r, c in posicoes_peoes}
    for r, c in posicoes_peoes:
        if sum(1 for r2, c2 in posicoes_peoes if c2 == c) > 1: pontuacao -= 15
        if (c - 1 not in colunas_com_peoes) and (c + 1 not in colunas_com_peoes): pontuacao -= 20
    return pontuacao


def avaliar_mobilidade(tabuleiro, cor, historico, alvo_en_passant):
    return len(gerar_todos_movimentos_legais(tabuleiro, cor, historico, alvo_en_passant))


# --- Função de Avaliação Principal ---

def avaliar_tabuleiro(estado_jogo):
    fim_de_jogo = verificar_fim_de_jogo(estado_jogo['tabuleiro'], estado_jogo['turno'],
                                        estado_jogo['historico_movimento'], estado_jogo['contador_50_lances'],
                                        estado_jogo['historico_posicoes'], estado_jogo['alvo_en_passant'])
    if fim_de_jogo:
        if fim_de_jogo == "XEQUE-MATE":
            return -PONTUACAO_PECAS['K'] * 10 if estado_jogo['turno'] == 'branco' else PONTUACAO_PECAS['K'] * 10
        return 0

    pontuacao = 0;
    tabuleiro = estado_jogo['tabuleiro']
    historico = estado_jogo['historico_movimento'];
    alvo_ep = estado_jogo['alvo_en_passant']

    for r in range(8):
        for c in range(8):
            peca = tabuleiro[r][c]
            if peca != '.':
                p_tipo = peca.upper();
                valor_base = PONTUACAO_PECAS.get(p_tipo, 0)
                valor_posicional = 0
                if p_tipo in TABELAS_POSICAO:
                    tabela = TABELAS_POSICAO[p_tipo]
                    valor_posicional = tabela[r][c] if peca.isupper() else tabela[7 - r][c]
                if peca.isupper():
                    pontuacao += valor_base + valor_posicional
                else:
                    pontuacao -= (valor_base + valor_posicional)

    pontuacao += (avaliar_seguranca_rei(tabuleiro, 'branco') - avaliar_seguranca_rei(tabuleiro, 'preto'))
    pontuacao += (avaliar_estrutura_peoes(tabuleiro, 'branco') - avaliar_estrutura_peoes(tabuleiro, 'preto'))
    mobilidade_branca = avaliar_mobilidade(tabuleiro, 'branco', historico, alvo_ep);
    mobilidade_preta = avaliar_mobilidade(tabuleiro, 'preto', historico, alvo_ep)
    pontuacao += (mobilidade_branca - mobilidade_preta) * 2

    return pontuacao


# --- Algoritmos de Busca ---

def busca_quiescente(estado_jogo, alfa, beta, maximizando_jogador, tempo_inicio, tempo_limite):
    if time.time() - tempo_inicio > tempo_limite: raise TimeoutError

    avaliacao_parado = avaliar_tabuleiro(estado_jogo)
    if maximizando_jogador:
        if avaliacao_parado >= beta: return beta, None
        alfa = max(alfa, avaliacao_parado)
    else:
        if avaliacao_parado <= alfa: return alfa, None
        beta = min(beta, avaliacao_parado)

    movimentos_captura = [mov for mov in gerar_todos_movimentos_legais(estado_jogo['tabuleiro'], estado_jogo['turno'],
                                                                       estado_jogo['historico_movimento'],
                                                                       estado_jogo['alvo_en_passant']) if
                          estado_jogo['tabuleiro'][mov[1][0]][mov[1][1]] != '.' or mov[1] == estado_jogo[
                              'alvo_en_passant']]
    if not movimentos_captura: return avaliacao_parado, None
    for movimento in movimentos_captura:
        novo_estado = simular_movimento_ia(estado_jogo, movimento)
        avaliacao, _ = busca_quiescente(novo_estado, alfa, beta, not maximizando_jogador, tempo_inicio, tempo_limite)
        if maximizando_jogador:
            if avaliacao >= beta: return beta, None
            alfa = max(alfa, avaliacao)
        else:
            if avaliacao <= alfa: return alfa, None
            beta = min(beta, avaliacao)
    return alfa if maximizando_jogador else beta, None


def minimax(estado_jogo, profundidade, alfa, beta, maximizando_jogador, tempo_inicio, tempo_limite):
    if time.time() - tempo_inicio > tempo_limite: raise TimeoutError

    fim_de_jogo = verificar_fim_de_jogo(estado_jogo['tabuleiro'], estado_jogo['turno'],
                                        estado_jogo['historico_movimento'], estado_jogo['contador_50_lances'],
                                        estado_jogo['historico_posicoes'], estado_jogo['alvo_en_passant'])
    if profundidade == 0 or fim_de_jogo:
        return busca_quiescente(estado_jogo, alfa, beta, maximizando_jogador, tempo_inicio, tempo_limite)

    movimentos_possiveis = gerar_todos_movimentos_legais(estado_jogo['tabuleiro'], estado_jogo['turno'],
                                                         estado_jogo['historico_movimento'],
                                                         estado_jogo['alvo_en_passant'])
    if not movimentos_possiveis: return avaliar_tabuleiro(estado_jogo), None

    melhor_movimento = random.choice(movimentos_possiveis)
    if maximizando_jogador:
        max_avaliacao = -float('inf')
        for movimento in movimentos_possiveis:
            novo_estado = simular_movimento_ia(estado_jogo, movimento)
            avaliacao, _ = minimax(novo_estado, profundidade - 1, alfa, beta, False, tempo_inicio, tempo_limite)
            if avaliacao > max_avaliacao: max_avaliacao, melhor_movimento = avaliacao, movimento
            alfa = max(alfa, avaliacao)
            if beta <= alfa: break
        return max_avaliacao, melhor_movimento
    else:
        min_avaliacao = float('inf')
        for movimento in movimentos_possiveis:
            novo_estado = simular_movimento_ia(estado_jogo, movimento)
            avaliacao, _ = minimax(novo_estado, profundidade - 1, alfa, beta, True, tempo_inicio, tempo_limite)
            if avaliacao < min_avaliacao: min_avaliacao, melhor_movimento = avaliacao, movimento
            beta = min(beta, avaliacao)
            if beta <= alfa: break
        return min_avaliacao, melhor_movimento


def encontrar_melhor_movimento(estado_jogo, tempo_limite_segundos):
    turno_ia = estado_jogo['turno'];
    maximizando = (turno_ia == 'branco')
    tempo_inicio = time.time();
    profundidade = 1;
    melhor_movimento_final = None

    while True:
        try:
            tempo_decorrido = time.time() - tempo_inicio
            if tempo_decorrido >= tempo_limite_segundos: break

            print(f"INFO: Buscando na profundidade {profundidade}...")
            _, melhor_movimento_iteracao = minimax(copy.deepcopy(estado_jogo), profundidade, -float('inf'),
                                                   float('inf'), maximizando, tempo_inicio, tempo_limite_segundos)

            if melhor_movimento_iteracao:
                melhor_movimento_final = melhor_movimento_iteracao
            else:
                break
            profundidade += 1
        except TimeoutError:
            print(f"INFO: Tempo limite atingido. Usando melhor movimento da profundidade {profundidade - 1}.")
            break

    if melhor_movimento_final is None:
        movimentos_possiveis = gerar_todos_movimentos_legais(estado_jogo['tabuleiro'], turno_ia,
                                                             estado_jogo['historico_movimento'],
                                                             estado_jogo['alvo_en_passant'])
        return random.choice(movimentos_possiveis) if movimentos_possiveis else None
    return melhor_movimento_final


def simular_movimento_ia(estado_original, movimento):
    estado = copy.deepcopy(estado_original)
    tabuleiro, turno_atual, historico, alvo_ep = estado['tabuleiro'], estado['turno'], estado['historico_movimento'], \
    estado['alvo_en_passant']
    linha_inicio, col_inicio = movimento[0];
    linha_fim, col_fim = movimento[1]
    peca = tabuleiro[linha_inicio][col_inicio]
    foi_captura = tabuleiro[linha_fim][col_fim] != '.' or (peca.lower() == 'p' and (linha_fim, col_fim) == alvo_ep)

    if peca == 'K':
        historico['K'] = True
    elif peca == 'k':
        historico['k'] = True
    elif peca == 'R' and linha_inicio == 7 and col_inicio == 0:
        historico['R_a1'] = True
    elif peca == 'R' and linha_inicio == 7 and col_inicio == 7:
        historico['R_h1'] = True
    elif peca == 'r' and linha_inicio == 0 and col_inicio == 0:
        historico['r_a8'] = True
    elif peca == 'r' and linha_inicio == 0 and col_inicio == 7:
        historico['r_h8'] = True

    if peca.lower() == 'p' and (linha_fim, col_fim) == alvo_ep:
        tabuleiro[linha_fim + (1 if turno_atual == 'branco' else -1)][col_fim] = '.'
    tabuleiro[linha_inicio][col_inicio] = '.';
    peca_final = peca
    if peca.lower() == 'p' and (linha_fim == 0 or linha_fim == 7):
        peca_final = 'Q' if turno_atual == 'branco' else 'q'
    tabuleiro[linha_fim][col_fim] = peca_final
    if peca.lower() == 'k' and abs(col_inicio - col_fim) == 2:
        if col_fim == 6:
            torre = tabuleiro[linha_fim][7]; tabuleiro[linha_fim][7] = '.'; tabuleiro[linha_fim][5] = torre
        elif col_fim == 2:
            torre = tabuleiro[linha_fim][0]; tabuleiro[linha_fim][0] = '.'; tabuleiro[linha_fim][3] = torre

    if peca.lower() == 'p' or foi_captura:
        estado['contador_50_lances'] = 0
    else:
        estado['contador_50_lances'] += 1
    estado['alvo_en_passant'] = ((linha_inicio + linha_fim) // 2, col_inicio) if peca.lower() == 'p' and abs(
        linha_inicio - linha_fim) == 2 else None
    estado['turno'] = 'preto' if turno_atual == 'branco' else 'branco'
    hash_atual = gerar_hash_posicao(tabuleiro, estado['turno'], historico, estado['alvo_en_passant'])
    estado['historico_posicoes'][hash_atual] = estado['historico_posicoes'].get(hash_atual, 0) + 1
    estado['fim_de_jogo'] = verificar_fim_de_jogo(tabuleiro, estado['turno'], historico, estado['contador_50_lances'],
                                                  estado['historico_posicoes'], estado['alvo_en_passant'])
    return estado