# logica_movimento.py (Corrigido)

# --- Funções de verificação de caminho ---

def caminho_livre_vertical(tabuleiro, inicio, fim):
    """Verifica se o caminho vertical entre inicio e fim está livre."""
    r_ini, c_ini = inicio
    r_fim, _ = fim
    passo = 1 if r_fim > r_ini else -1
    for r in range(r_ini + passo, r_fim, passo):
        if tabuleiro[r][c_ini] != '.':
            return False
    return True


def caminho_livre_horizontal(tabuleiro, inicio, fim):
    """Verifica se o caminho horizontal entre inicio e fim está livre."""
    r_ini, c_ini = inicio
    _, c_fim = fim
    passo = 1 if c_fim > c_ini else -1
    for c in range(c_ini + passo, c_fim, passo):
        if tabuleiro[r_ini][c] != '.':
            return False
    return True


def caminho_livre_diagonal(tabuleiro, inicio, fim):
    """Verifica se o caminho diagonal entre inicio e fim está livre."""
    r_ini, c_ini = inicio
    r_fim, c_fim = fim
    passo_r = 1 if r_fim > r_ini else -1
    passo_c = 1 if c_fim > c_ini else -1
    r, c = r_ini + passo_r, c_ini + passo_c
    while r != r_fim:
        if tabuleiro[r][c] != '.':
            return False
        r += passo_r
        c += passo_c
    return True


# --- Funções principais de validação ---

def casa_esta_sob_ataque(tabuleiro, posicao, cor_defensora, historico):
    """Verifica se a 'posicao' está sob ataque por peças da cor oposta."""
    cor_atacante = 'preto' if cor_defensora == 'branco' else 'branco'
    for r_ini in range(8):
        for c_ini in range(8):
            peca_atacante = tabuleiro[r_ini][c_ini]
            if peca_atacante != '.' and ((cor_atacante == 'branco' and peca_atacante.isupper()) or (
                    cor_atacante == 'preto' and peca_atacante.islower())):
                # Chamamos eh_movimento_valido em modo de "verificação de ataque" para quebrar o ciclo de recursão.
                if eh_movimento_valido(tabuleiro, (r_ini, c_ini), posicao, cor_atacante, None, None,
                                       verificando_ataque=True):
                    return True
    return False


def validar_movimento_peao(tabuleiro, inicio, fim, cor_peca, historico, alvo_en_passant, verificando_ataque=False):
    r_ini, c_ini = inicio
    r_fim, c_fim = fim
    direcao = -1 if cor_peca == 'branco' else 1
    linha_inicial = 6 if cor_peca == 'branco' else 1

    # Movimento para frente
    if c_ini == c_fim and tabuleiro[r_fim][c_fim] == '.':
        if r_ini + direcao == r_fim: return True
        if r_ini == linha_inicial and r_ini + 2 * direcao == r_fim and tabuleiro[r_ini + direcao][
            c_ini] == '.': return True

    # Captura
    if abs(c_ini - c_fim) == 1 and r_ini + direcao == r_fim:
        peca_no_destino = tabuleiro[r_fim][c_fim]
        # Captura normal
        if peca_no_destino != '.' and (peca_no_destino.isupper() != (cor_peca == 'branco')): return True
        # Captura En Passant
        if (r_fim, c_fim) == alvo_en_passant: return True
        # Durante a verificação de ataque, a captura diagonal é um ataque mesmo sem peça no destino.
        if verificando_ataque and peca_no_destino == '.': return True

    return False


def validar_movimento_torre(tabuleiro, inicio, fim, cor_peca, historico, alvo_en_passant, verificando_ataque=False):
    r_ini, c_ini = inicio
    r_fim, c_fim = fim
    if r_ini == r_fim: return caminho_livre_horizontal(tabuleiro, inicio, fim)
    if c_ini == c_fim: return caminho_livre_vertical(tabuleiro, inicio, fim)
    return False


def validar_movimento_bispo(tabuleiro, inicio, fim, cor_peca, historico, alvo_en_passant, verificando_ataque=False):
    r_ini, c_ini = inicio
    r_fim, c_fim = fim
    if abs(r_ini - r_fim) == abs(c_ini - c_fim): return caminho_livre_diagonal(tabuleiro, inicio, fim)
    return False


def validar_movimento_cavalo(tabuleiro, inicio, fim, cor_peca, historico, alvo_en_passant, verificando_ataque=False):
    r_ini, c_ini = inicio
    r_fim, c_fim = fim
    dr = abs(r_ini - r_fim)
    dc = abs(c_ini - c_fim)
    return (dr == 2 and dc == 1) or (dr == 1 and dc == 2)


def validar_movimento_rainha(tabuleiro, inicio, fim, cor_peca, historico, alvo_en_passant, verificando_ataque=False):
    return validar_movimento_torre(tabuleiro, inicio, fim, cor_peca, historico, alvo_en_passant) or \
        validar_movimento_bispo(tabuleiro, inicio, fim, cor_peca, historico, alvo_en_passant)


def validar_movimento_roque(tabuleiro, inicio, fim, cor, historico):
    r_ini, c_ini = inicio
    r_fim, c_fim = fim
    # Condições básicas
    if esta_em_xeque(tabuleiro, cor, historico): return False

    rei_moveu = historico.get('K' if cor == 'branco' else 'k', True)
    if rei_moveu: return False

    # Roque Curto (lado do rei)
    if c_fim == 6:
        torre_moveu = historico.get('R_h1' if cor == 'branco' else 'r_h8', True)
        if torre_moveu: return False
        if not caminho_livre_horizontal(tabuleiro, (r_ini, c_ini), (r_fim, 7)): return False
        if casa_esta_sob_ataque(tabuleiro, (r_ini, 5), cor, historico): return False  # Casa de passagem
        return True

    # Roque Longo (lado da rainha)
    if c_fim == 2:
        torre_moveu = historico.get('R_a1' if cor == 'branco' else 'r_a8', True)
        if torre_moveu: return False
        if not caminho_livre_horizontal(tabuleiro, (r_ini, c_ini), (r_fim, 0)): return False
        if casa_esta_sob_ataque(tabuleiro, (r_ini, 3), cor, historico): return False  # Casa de passagem
        return True

    return False


def validar_movimento_rei(tabuleiro, inicio, fim, cor_peca, historico, alvo_en_passant, verificando_ataque=False):
    r_ini, c_ini = inicio
    r_fim, c_fim = fim
    dist_linha = abs(r_ini - r_fim)
    dist_col = abs(c_ini - c_fim)

    # A validação de roque NUNCA deve ser chamada durante uma verificação de ataque para evitar recursão.
    if not verificando_ataque and dist_col == 2 and dist_linha == 0:
        return validar_movimento_roque(tabuleiro, inicio, fim, cor_peca, historico)

    # Movimento normal de 1 casa
    return dist_linha <= 1 and dist_col <= 1


# --- Função principal de despacho ---

def eh_movimento_valido(tabuleiro, inicio, fim, turno, historico=None, alvo_en_passant=None, verificando_ataque=False):
    """
    Verifica se um movimento é válido de acordo com as regras do xadrez.
    'verificando_ataque' é um flag para quebrar a recursão infinita.
    """
    if inicio == fim: return False
    r_ini, c_ini = inicio
    peca = tabuleiro[r_ini][c_ini]
    if peca == '.': return False

    cor_peca = 'branco' if peca.isupper() else 'preto'
    if not verificando_ataque and cor_peca != turno: return False

    r_fim, c_fim = fim
    peca_destino = tabuleiro[r_fim][c_fim]
    if peca_destino != '.' and (peca_destino.isupper() == peca.isupper()):
        return False

    tipo_peca = peca.lower()

    funcoes_validacao = {
        'p': validar_movimento_peao, 'r': validar_movimento_torre,
        'n': validar_movimento_cavalo, 'b': validar_movimento_bispo,
        'q': validar_movimento_rainha, 'k': validar_movimento_rei
    }

    if tipo_peca in funcoes_validacao:
        # Passa o flag 'verificando_ataque' para a função específica
        return funcoes_validacao[tipo_peca](tabuleiro, inicio, fim, cor_peca, historico, alvo_en_passant,
                                            verificando_ataque)

    return False


# Importação no final para evitar importação circular
from regras_jogo import esta_em_xeque