# testes_regras.py

from tabuleiro import criar_tabuleiro_inicial
from utils import converter_notacao_para_indices
from logica_movimento import eh_movimento_valido
from regras_jogo import verificar_fim_de_jogo, esta_em_xeque, gerar_hash_posicao, gerar_todos_movimentos_legais, verificar_material_insuficiente

def executar_sequencia_de_movimentos(movimentos):
    estado_jogo = {
        'tabuleiro': criar_tabuleiro_inicial(), 'turno': 'branco',
        'historico_movimento': {'K': False, 'R_a1': False, 'R_h1': False, 'k': False, 'r_a8': False, 'r_h8': False},
        'alvo_en_passant': None, 'contador_50_lances': 0, 'historico_posicoes': {}
    }
    hash_inicial = gerar_hash_posicao(estado_jogo['tabuleiro'], estado_jogo['turno'], estado_jogo['historico_movimento'], estado_jogo['alvo_en_passant'])
    estado_jogo['historico_posicoes'][hash_inicial] = 1
    for mov_str in movimentos:
        tabuleiro, turno_atual, historico, alvo_ep = estado_jogo['tabuleiro'], estado_jogo['turno'], estado_jogo['historico_movimento'], estado_jogo['alvo_en_passant']
        inicio_notacao, fim_notacao = mov_str[0:2], mov_str[2:4]
        linha_inicio, col_inicio = converter_notacao_para_indices(inicio_notacao)
        linha_fim, col_fim = converter_notacao_para_indices(fim_notacao)
        if linha_inicio is None: continue
        peca = tabuleiro[linha_inicio][col_inicio]
        foi_captura = tabuleiro[linha_fim][col_fim] != '.' or (peca.lower() == 'p' and (linha_fim, col_fim) == alvo_ep)
        if peca == 'K': historico['K'] = True
        elif peca == 'k': historico['k'] = True
        elif peca == 'R' and linha_inicio == 7 and col_inicio == 0: historico['R_a1'] = True
        elif peca == 'R' and linha_inicio == 7 and col_inicio == 7: historico['R_h1'] = True
        elif peca == 'r' and linha_inicio == 0 and col_inicio == 0: historico['r_a8'] = True
        elif peca == 'r' and linha_inicio == 0 and col_inicio == 7: historico['r_h8'] = True
        if peca.lower() == 'p' or foi_captura: estado_jogo['contador_50_lances'] = 0
        else: estado_jogo['contador_50_lances'] += 1
        if peca.lower() == 'p' and (linha_fim, col_fim) == alvo_ep: tabuleiro[linha_fim + (1 if turno_atual == 'branco' else -1)][col_fim] = '.'
        estado_jogo['alvo_en_passant'] = ((linha_inicio + linha_fim) // 2, col_inicio) if peca.lower() == 'p' and abs(linha_inicio - linha_fim) == 2 else None
        tabuleiro[linha_inicio][col_inicio] = '.'; tabuleiro[linha_fim][col_fim] = peca
        estado_jogo['turno'] = 'preto' if turno_atual == 'branco' else 'branco'
        hash_novo = gerar_hash_posicao(tabuleiro, estado_jogo['turno'], historico, estado_jogo['alvo_en_passant'])
        estado_jogo['historico_posicoes'][hash_novo] = estado_jogo['historico_posicoes'].get(hash_novo, 0) + 1
    return estado_jogo

def testar_roque():
    print("--- INICIANDO TESTES DE ROQUE ---")
    sequencia = ['e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1c4', 'd7d6']
    estado = executar_sequencia_de_movimentos(sequencia)
    inicio, fim = converter_notacao_para_indices('e1'), converter_notacao_para_indices('g1')
    assert eh_movimento_valido(estado['tabuleiro'], inicio, fim, estado['turno'], estado['historico_movimento'], estado['alvo_en_passant'])
    print("✅ Testes de Roque passaram.")

def testar_promocao_peao():
    print("\n--- INICIANDO TESTES DE PROMOÇÃO DE PEÃO ---")
    tabuleiro_b = [['.'] * 8 for _ in range(8)]; tabuleiro_b[1][2] = 'P';
    inicio_b, fim_b_reto = converter_notacao_para_indices('c7'), converter_notacao_para_indices('c8')
    assert eh_movimento_valido(tabuleiro_b, inicio_b, fim_b_reto, 'branco', {}, None)
    print("✅ Testes de pré-condição de promoção passaram com sucesso!")

def testar_en_passant():
    print("\n--- INICIANDO TESTES DE EN PASSANT ---")
    sequencia = ['e2e4', 'a7a6', 'e4e5', 'd7d5']
    estado = executar_sequencia_de_movimentos(sequencia)
    inicio, fim = converter_notacao_para_indices('e5'), converter_notacao_para_indices('d6')
    assert eh_movimento_valido(estado['tabuleiro'], inicio, fim, estado['turno'], estado['historico_movimento'], estado['alvo_en_passant'])
    print("✅ Todos os testes de en passant passaram com sucesso!")

def testar_empate_afogamento():
    print("\n--- INICIANDO TESTES DE EMPATE (AFOGAMENTO) ---")
    estado_jogo = {'tabuleiro': [['.'] * 8 for _ in range(8)], 'turno': 'branco', 'historico_movimento': {'K': False, 'R_a1': False, 'R_h1': False, 'k': False, 'r_a8': False, 'r_h8': False}, 'alvo_en_passant': None, 'contador_50_lances': 0, 'historico_posicoes': {}}
    tabuleiro = estado_jogo['tabuleiro']; tabuleiro[7][7] = 'K'; tabuleiro[5][6] = 'q'; tabuleiro[0][0] = 'k'
    resultado = verificar_fim_de_jogo(tabuleiro, 'branco', estado_jogo['historico_movimento'], 0, {}, None)
    assert resultado == "EMPATE_AFOGAMENTO"
    print("✅ Todos os testes de empate por afogamento passaram com sucesso!")

def testar_regra_50_lances():
    print("\n--- INICIANDO TESTES DA REGRA DOS 50 LANCES ---")
    sequencia_repetitiva = ['b1c3', 'b8c6', 'c3b1', 'c6b8'] * 25
    estado = executar_sequencia_de_movimentos(sequencia_repetitiva)
    resultado = verificar_fim_de_jogo(estado['tabuleiro'], estado['turno'], estado['historico_movimento'], estado['contador_50_lances'], estado['historico_posicoes'], estado['alvo_en_passant'])
    assert estado['contador_50_lances'] >= 100
    assert resultado == "EMPATE_50_LANCES"
    print("✅ Todos os testes da regra dos 50 lances passaram com sucesso!")

def testar_repeticao_tripla():
    print("\n--- INICIANDO TESTES DE REPETIÇÃO TRIPLA ---")
    sequencia_repetitiva = ['g1f3', 'g8f6', 'f3g1', 'f6g8'] * 2
    estado = executar_sequencia_de_movimentos(sequencia_repetitiva)
    resultado = verificar_fim_de_jogo(estado['tabuleiro'], estado['turno'], estado['historico_movimento'], estado['contador_50_lances'], estado['historico_posicoes'], estado['alvo_en_passant'])
    assert resultado == "EMPATE_REPETICAO"
    print("✅ Todos os testes de repetição tripla passaram com sucesso!")


def testar_material_insuficiente():
    print("\n--- INICIANDO TESTES DE MATERIAL INSUFICIENTE ---")

    # Cenário 1: Rei vs Rei - EMPATE
    tabuleiro_kvk = [['.'] * 8 for _ in range(8)]
    tabuleiro_kvk[0][4] = 'k';
    tabuleiro_kvk[7][4] = 'K'
    assert verificar_material_insuficiente(tabuleiro_kvk) == True, "Falha: Rei vs Rei deveria ser empate."

    # Cenário 2: Rei vs Rei e Cavalo - EMPATE
    tabuleiro_kvkn = [['.'] * 8 for _ in range(8)]
    tabuleiro_kvkn[0][4] = 'k';
    tabuleiro_kvkn[7][4] = 'K';
    tabuleiro_kvkn[5][5] = 'N'
    assert verificar_material_insuficiente(tabuleiro_kvkn) == True, "Falha: Rei vs Rei e Cavalo deveria ser empate."

    # Cenário 3: Rei e Bispo vs Rei e Bispo (mesma cor) - EMPATE
    tabuleiro_kbvkb_mesma = [['.'] * 8 for _ in range(8)]
    tabuleiro_kbvkb_mesma[0][4] = 'k';
    tabuleiro_kbvkb_mesma[7][4] = 'K'
    tabuleiro_kbvkb_mesma[3][3] = 'B'  # d5 (casa preta)
    tabuleiro_kbvkb_mesma[4][4] = 'b'  # e4 (casa preta)
    assert verificar_material_insuficiente(
        tabuleiro_kbvkb_mesma) == True, "Falha: K+B vs K+B na mesma cor deveria ser empate."

    # Cenário 4: Com uma Torre - NÃO É EMPATE
    tabuleiro_torre = [['.'] * 8 for _ in range(8)]
    tabuleiro_torre[0][4] = 'k';
    tabuleiro_torre[7][4] = 'K';
    tabuleiro_torre[5][5] = 'R'
    assert verificar_material_insuficiente(
        tabuleiro_torre) == False, "Falha: Presença de uma Torre não deveria ser empate."

    # Cenário 5: Com um Peão - NÃO É EMPATE
    tabuleiro_peao = [['.'] * 8 for _ in range(8)]
    tabuleiro_peao[0][4] = 'k';
    tabuleiro_peao[7][4] = 'K';
    tabuleiro_peao[6][4] = 'P'
    assert verificar_material_insuficiente(
        tabuleiro_peao) == False, "Falha: Presença de um Peão não deveria ser empate."

    print("✅ Todos os testes de material insuficiente passaram com sucesso!")

if __name__ == "__main__":
    testar_roque()
    testar_promocao_peao()
    testar_en_passant()
    testar_empate_afogamento()
    testar_regra_50_lances()
    testar_repeticao_tripla()
    testar_material_insuficiente()