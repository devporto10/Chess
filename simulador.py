# simulador.py

import copy
import time
from tabuleiro import criar_tabuleiro_inicial, exibir_tabuleiro
from utils import converter_notacao_para_indices
from logica_movimento import eh_movimento_valido
from regras_jogo import esta_em_xeque, verificar_fim_de_jogo, gerar_hash_posicao


def simular_partida(lances, delay=1.0):
    """
    Executa uma partida pré-definida lance a lance e imprime o resultado.
    """
    print("--- INICIANDO SIMULAÇÃO DE PARTIDA HISTÓRICA ---")

    estado_jogo = {
        'tabuleiro': criar_tabuleiro_inicial(), 'turno': 'branco',
        'historico_movimento': {'K': False, 'R_a1': False, 'R_h1': False, 'k': False, 'r_a8': False, 'r_h8': False},
        'alvo_en_passant': None, 'contador_50_lances': 0, 'historico_posicoes': {}
    }
    hash_inicial = gerar_hash_posicao(estado_jogo['tabuleiro'], estado_jogo['turno'],
                                      estado_jogo['historico_movimento'], estado_jogo['alvo_en_passant'])
    estado_jogo['historico_posicoes'][hash_inicial] = 1

    numero_lance = 1
    numero_meio_lance = 0

    for movimento_str in lances:
        tabuleiro = estado_jogo['tabuleiro']
        turno_atual = estado_jogo['turno']
        historico = estado_jogo['historico_movimento']
        alvo_ep = estado_jogo['alvo_en_passant']

        numero_meio_lance += 1
        if numero_meio_lance % 2 != 0:
            print(f"\n----------------- Lance {numero_lance} -----------------")

        exibir_tabuleiro(tabuleiro)
        print(f"Turno {numero_meio_lance} ({turno_atual.capitalize()}): {movimento_str}")

        inicio_notacao, fim_notacao = movimento_str[0:2], movimento_str[2:4]
        linha_inicio, col_inicio = converter_notacao_para_indices(inicio_notacao)
        linha_fim, col_fim = converter_notacao_para_indices(fim_notacao)

        if not eh_movimento_valido(tabuleiro, (linha_inicio, col_inicio), (linha_fim, col_fim), turno_atual, historico,
                                   alvo_ep):
            print(f"ERRO DE VALIDAÇÃO! O motor considerou o lance {movimento_str} inválido.")
            break

        peca = tabuleiro[linha_inicio][col_inicio]
        foi_captura = tabuleiro[linha_fim][col_fim] != '.' or (peca.lower() == 'p' and (linha_fim, col_fim) == alvo_ep)

        ### CORREÇÃO: Bloco if/elif reescrito com a sintaxe correta ###
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

        tabuleiro[linha_inicio][col_inicio] = '.'
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
            estado_jogo['contador_50_lances'] = 0
        else:
            estado_jogo['contador_50_lances'] += 1
        estado_jogo['alvo_en_passant'] = ((linha_inicio + linha_fim) // 2, col_inicio) if peca.lower() == 'p' and abs(
            linha_inicio - linha_fim) == 2 else None

        estado_jogo['turno'] = 'preto' if turno_atual == 'branco' else 'branco'

        if turno_atual == 'preto':
            numero_lance += 1

        time.sleep(delay)

    exibir_tabuleiro(estado_jogo['tabuleiro'])
    print("\n--- FIM DA SIMULAÇÃO ---")


if __name__ == "__main__":
    partida_kasparov_vs_deepblue_1997_g6 = [
        'e2e4', 'c7c6',
        'd2d4', 'd7d5',
        'b1c3', 'd5e4',
        'c3e4', 'b8d7',
        'e4g5', 'g8f6',
        'f1d3', 'e7e6',
        'g1f3', 'h7h6',
        'g5e6', 'd8e7',
        'e1g1',  # Roque
        'f7e6',
        'd3g6',  # Xeque
        'e8d8',
        'c1f4', 'b7b5',
        'a2a4', 'c8b7',
        'f1e1', 'f6d5',
        'f4g3',  # Lance 14 das Brancas (Bg3)
        'd8c8',
        'a4b5', 'c6b5',
        'd1d3', 'b7c6',
        'g6f5',  # Lance 17 das Brancas (Bf5, o bispo de g6 se move)
        'e6f5',
        'e1e7', 'f8e7',
        'c2c4'
    ]

    simular_partida(partida_kasparov_vs_deepblue_1997_g6, delay=0.5)