# regras_jogo.py

import copy
from logica_movimento import eh_movimento_valido, casa_esta_sob_ataque

# Adicione a importação do nosso novo arquivo de IA
try:
    from ia import PONTUACAO_PECAS
except ImportError:
    PONTUACAO_PECAS = {} # Fallback para evitar erro


def avaliar_tabuleiro(tabuleiro):
    """
    Calcula a pontuação do tabuleiro.
    Valores positivos favorecem as brancas, negativos favorecem as pretas.
    """
    pontuacao = 0
    for linha in tabuleiro:
        for peca in linha:
            if peca.isupper(): # Peça branca
                pontuacao += PONTUACAO_PECAS.get(peca, 0)
            elif peca.islower(): # Peça preta
                pontuacao -= PONTUACAO_PECAS.get(peca.upper(), 0)
    return pontuacao

def encontrar_posicao_rei(tabuleiro, cor):
    peca_rei = 'K' if cor == 'branco' else 'k'
    for linha_idx, linha in enumerate(tabuleiro):
        for col_idx, peca in enumerate(linha):
            if peca == peca_rei:
                return (linha_idx, col_idx)
    return None


def esta_em_xeque(tabuleiro, cor_rei, historico):
    posicao_rei = encontrar_posicao_rei(tabuleiro, cor_rei)
    if not posicao_rei: return False
    return casa_esta_sob_ataque(tabuleiro, posicao_rei, cor_rei, historico)


def gerar_hash_posicao(tabuleiro, turno, historico_roque, alvo_en_passant):
    """
    Cria uma string única (hash) de COMPRIMENTO FIXO que representa o estado.
    """
    # 1. Posição das peças (64 caracteres)
    hash_tabuleiro = "".join("".join(linha) for linha in tabuleiro)

    # 2. De quem é a vez (1 caractere)
    hash_turno = turno[0]

    # 3. Direitos de roque (4 caracteres)
    hash_roque = ""
    hash_roque += 'K' if not historico_roque['K'] and not historico_roque['R_h1'] else '-'
    hash_roque += 'Q' if not historico_roque['K'] and not historico_roque['R_a1'] else '-'
    hash_roque += 'k' if not historico_roque['k'] and not historico_roque['r_h8'] else '-'
    hash_roque += 'q' if not historico_roque['k'] and not historico_roque['r_a8'] else '-'

    # 4. Alvo de en passant (4 caracteres, ex: "(r,c)" -> "5,4-", ou "----")
    if alvo_en_passant:
        hash_en_passant = f"{alvo_en_passant[0]},{alvo_en_passant[1]}".ljust(4, '-')
    else:
        hash_en_passant = "----"

    # Total: 64 + 1 + 4 + 4 = 73 caracteres
    return f"{hash_tabuleiro}|{hash_turno}|{hash_roque}|{hash_en_passant}"


def gerar_todos_movimentos_legais(tabuleiro, cor, historico, alvo_en_passant):
    movimentos_legais = []
    for linha_inicio in range(8):
        for col_inicio in range(8):
            peca = tabuleiro[linha_inicio][col_inicio]
            if peca != '.' and ((cor == 'branco' and peca.isupper()) or (cor == 'preto' and peca.islower())):
                for linha_fim in range(8):
                    for col_fim in range(8):
                        inicio, fim = (linha_inicio, col_inicio), (linha_fim, col_fim)
                        if eh_movimento_valido(tabuleiro, inicio, fim, cor, historico, alvo_en_passant):
                            tabuleiro_simulado = copy.deepcopy(tabuleiro)
                            peca_movida = tabuleiro_simulado[linha_inicio][col_inicio]
                            tabuleiro_simulado[linha_inicio][col_inicio] = '.'
                            tabuleiro_simulado[linha_fim][col_fim] = peca_movida
                            if not esta_em_xeque(tabuleiro_simulado, cor, historico):
                                movimentos_legais.append((inicio, fim))
    return movimentos_legais


### MUDANÇA: Adicionamos a nova função de verificação de material ###
def verificar_material_insuficiente(tabuleiro):
    """Verifica se há material suficiente no tabuleiro para um xeque-mate."""
    pecas_brancas, pecas_pretas = [], []
    posicoes_bispos_brancos, posicoes_bispos_pretos = [], []

    for r, linha in enumerate(tabuleiro):
        for c, peca in enumerate(linha):
            p_lower = peca.lower()
            # Se houver uma Rainha, Torre ou Peão, há material suficiente.
            if p_lower in ['q', 'r', 'p']:
                return False

            if p_lower in ['n', 'b']:
                if peca.isupper():
                    pecas_brancas.append(p_lower)
                    if p_lower == 'b': posicoes_bispos_brancos.append((r, c))
                else:
                    pecas_pretas.append(p_lower)
                    if p_lower == 'b': posicoes_bispos_pretos.append((r, c))

    # Cenários de empate:
    # K vs K
    if not pecas_brancas and not pecas_pretas: return True
    # K vs K+N ou K vs K+B
    if (not pecas_brancas and len(pecas_pretas) == 1) or \
            (len(pecas_brancas) == 1 and not pecas_pretas): return True
    # K+B vs K+B (ambos os bispos na mesma cor de casa)
    if pecas_brancas == ['b'] and pecas_pretas == ['b']:
        r1, c1 = posicoes_bispos_brancos[0]
        r2, c2 = posicoes_bispos_pretos[0]
        # Se a soma das coordenadas tem a mesma paridade, os bispos estão na mesma cor
        if (r1 + c1) % 2 == (r2 + c2) % 2:
            return True

    return False


### MUDANÇA: A função principal agora chama a verificação de material ###
def verificar_fim_de_jogo(tabuleiro, cor_jogador, historico, contador_50_lances, historico_posicoes, alvo_en_passant):
    """Verifica todas as condições de fim de jogo."""
    if contador_50_lances >= 100: return "EMPATE_50_LANCES"
    if verificar_material_insuficiente(tabuleiro): return "EMPATE_MATERIAL"
    for contagem in historico_posicoes.values():
        if contagem >= 3: return "EMPATE_REPETICAO"

    movimentos_possiveis = gerar_todos_movimentos_legais(tabuleiro, cor_jogador, historico, alvo_en_passant)
    if not movimentos_possiveis:
        if esta_em_xeque(tabuleiro, cor_jogador, historico):
            return "XEQUE-MATE"
        else:
            return "EMPATE_AFOGAMENTO"
    return None


# regras_jogo.py

# ... (adicionar ao final do arquivo) ...

def executar_movimento(estado_jogo, movimento):
    """
    Executa um movimento e retorna o novo estado do jogo.
    Esta é a função canônica para atualização de estado.
    """
    novo_estado = copy.deepcopy(estado_jogo)
    tabuleiro = novo_estado['tabuleiro']
    historico = novo_estado['historico_movimento']
    turno_atual = novo_estado['turno']

    linha_inicio, col_inicio = movimento[0]
    linha_fim, col_fim = movimento[1]

    peca = tabuleiro[linha_inicio][col_inicio]
    peca_capturada = tabuleiro[linha_fim][col_fim]
    alvo_ep_anterior = novo_estado['alvo_en_passant']

    # Atualiza histórico de movimento para o roque
    if peca == 'K':
        historico['K'] = True
    elif peca == 'k':
        historico['k'] = True
    elif peca == 'R' and (linha_inicio, col_inicio) == (7, 0):
        historico['R_a1'] = True
    elif peca == 'R' and (linha_inicio, col_inicio) == (7, 7):
        historico['R_h1'] = True
    elif peca == 'r' and (linha_inicio, col_inicio) == (0, 0):
        historico['r_a8'] = True
    elif peca == 'r' and (linha_inicio, col_inicio) == (0, 7):
        historico['r_h8'] = True

    # Lógica de Captura e En Passant
    foi_captura = peca_capturada != '.'
    foi_captura_ep = peca.lower() == 'p' and (linha_fim, col_fim) == alvo_ep_anterior

    if foi_captura_ep:
        # Remove o peão capturado no en passant
        tabuleiro[linha_inicio][col_fim] = '.'

    # Move a peça
    tabuleiro[linha_inicio][col_inicio] = '.'
    tabuleiro[linha_fim][col_fim] = peca

    # Lógica de Promoção (simplificada para Rainha, como no PGN processor)
    if peca.lower() == 'p' and (linha_fim == 0 or linha_fim == 7):
        nova_peca = 'Q' if turno_atual == 'branco' else 'q'
        tabuleiro[linha_fim][col_fim] = nova_peca

    # Lógica do Roque
    if peca.lower() == 'k' and abs(col_inicio - col_fim) == 2:
        if col_fim == 6:  # Roque curto
            torre = tabuleiro[linha_fim][7]
            tabuleiro[linha_fim][7] = '.'
            tabuleiro[linha_fim][5] = torre
        elif col_fim == 2:  # Roque longo
            torre = tabuleiro[linha_fim][0]
            tabuleiro[linha_fim][0] = '.'
            tabuleiro[linha_fim][3] = torre

    # Atualiza regra dos 50 lances
    if peca.lower() == 'p' or foi_captura or foi_captura_ep:
        novo_estado['contador_50_lances'] = 0
    else:
        novo_estado['contador_50_lances'] += 1

    # Define o novo alvo de en passant
    if peca.lower() == 'p' and abs(linha_inicio - linha_fim) == 2:
        novo_estado['alvo_en_passant'] = ((linha_inicio + linha_fim) // 2, col_inicio)
    else:
        novo_estado['alvo_en_passant'] = None

    # Troca o turno
    novo_estado['turno'] = 'preto' if turno_atual == 'branco' else 'branco'

    # Atualiza histórico de posições para regra de repetição
    hash_novo = gerar_hash_posicao(tabuleiro, novo_estado['turno'], historico, novo_estado['alvo_en_passant'])
    novo_estado['historico_posicoes'][hash_novo] = novo_estado['historico_posicoes'].get(hash_novo, 0) + 1

    return novo_estado