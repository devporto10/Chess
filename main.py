# main.py

import copy
from tabuleiro import criar_tabuleiro_inicial, exibir_tabuleiro
from utils import converter_notacao_para_indices
from logica_movimento import eh_movimento_valido
from regras_jogo import esta_em_xeque, verificar_fim_de_jogo, gerar_hash_posicao


def jogar():
    """Função principal que executa o loop do jogo de xadrez."""

    print("--- Bem-vindo ao Xadrez de Console! ---")
    print("Use a notação de coordenadas (ex: 'e2e4'), '0-0'/'0-0-0' para roque, ou 'sair'.")

    estado_jogo = {
        'tabuleiro': criar_tabuleiro_inicial(), 'turno': 'branco',
        'historico_movimento': {'K': False, 'R_a1': False, 'R_h1': False, 'k': False, 'r_a8': False, 'r_h8': False},
        'alvo_en_passant': None, 'contador_50_lances': 0, 'historico_posicoes': {}
    }

    hash_inicial = gerar_hash_posicao(estado_jogo['tabuleiro'], estado_jogo['turno'],
                                      estado_jogo['historico_movimento'], estado_jogo['alvo_en_passant'])
    estado_jogo['historico_posicoes'][hash_inicial] = 1

    while True:
        tabuleiro, turno_atual, historico, alvo_ep = estado_jogo['tabuleiro'], estado_jogo['turno'], estado_jogo[
            'historico_movimento'], estado_jogo['alvo_en_passant']
        exibir_tabuleiro(tabuleiro);
        print(f"\nTurno do jogador: {turno_atual.capitalize()}")
        movimento_str = input("Seu movimento: ")

        if movimento_str.lower() == 'sair': print("\nJogo encerrado."); break
        if movimento_str.lower() in ['0-0', 'o-o']:
            movimento_str = 'e1g1' if turno_atual == 'branco' else 'e8g8'
        elif movimento_str.lower() in ['0-0-0', 'o-o-o']:
            movimento_str = 'e1c1' if turno_atual == 'branco' else 'e8c8'
        if len(movimento_str) != 4: print("ERRO: Formato inválido."); continue

        inicio_notacao, fim_notacao = movimento_str[0:2], movimento_str[2:4]
        linha_inicio, col_inicio = converter_notacao_para_indices(inicio_notacao)
        linha_fim, col_fim = converter_notacao_para_indices(fim_notacao)
        if linha_inicio is None: print("ERRO: Coordenadas inválidas."); continue

        peca = tabuleiro[linha_inicio][col_inicio]
        if peca == '.': print(f"ERRO: A casa '{inicio_notacao}' está vazia."); continue
        if (turno_atual == 'branco' and not peca.isupper()) or (turno_atual == 'preto' and not peca.islower()): print(
            f"ERRO: A peça em {inicio_notacao} não é sua."); continue
        if not eh_movimento_valido(tabuleiro, (linha_inicio, col_inicio), (linha_fim, col_fim), turno_atual, historico,
                                   alvo_ep): print("ERRO: Movimento ilegal para esta peça."); continue

        tabuleiro_simulado = copy.deepcopy(tabuleiro)
        tabuleiro_simulado[linha_inicio][col_inicio] = '.'
        tabuleiro_simulado[linha_fim][col_fim] = peca
        if esta_em_xeque(tabuleiro_simulado, turno_atual, historico):
            print("ERRO: Movimento ilegal, seu rei ficaria em xeque.");
            continue

        foi_captura = tabuleiro[linha_fim][col_fim] != '.' or (peca.lower() == 'p' and (linha_fim, col_fim) == alvo_ep)

        if peca == 'K': historico['K'] = True; elif
        peca == 'k': historico['k'] = True; elif peca == 'R' and linha_inicio == 7 and col_inicio == 0: historico[
            'R_a1'] = True; elif peca == 'R' and linha_inicio == 7 and col_inicio == 7: historico[
            'R_h1'] = True; elif peca == 'r' and linha_inicio == 0 and col_inicio == 0: historico[
            'r_a8'] = True; elif peca == 'r' and linha_inicio == 0 and col_inicio == 7: historico['r_h8'] = True

        if peca.lower() == 'p' and (linha_fim, col_fim) == alvo_ep:
        tabuleiro[linha_fim + (1 if turno_atual == 'branco' else -1)][col_fim] = '.'
        tabuleiro[linha_inicio][col_inicio] = '.'
        peca_final = peca
        if peca.lower() == 'p' and (linha_fim == 0 or linha_fim == 7):
            while True:
                escolha = input("Promover peão para (q, r, b, n): ").lower()
                if escolha in ['q', 'r', 'b', 'n']:
                    peca_final = escolha.upper() if turno_atual == 'branco' else escolha.lower(); break
                else:
                    print("Escolha inválida.")
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
        turno_seguinte = estado_jogo['turno']

        hash_atual = gerar_hash_posicao(tabuleiro, turno_seguinte, historico, estado_jogo['alvo_en_passant'])
        estado_jogo['historico_posicoes'][hash_atual] = estado_jogo['historico_posicoes'].get(hash_atual, 0) + 1

        estado_final = verificar_fim_de_jogo(tabuleiro, turno_seguinte, historico, estado_jogo['contador_50_lances'],
                                             estado_jogo['historico_posicoes'], estado_jogo['alvo_en_passant'])

        if estado_final:
            exibir_tabuleiro(tabuleiro)
            vencedor = 'Brancas' if turno_seguinte == 'preto' else 'Pretas'
            if estado_final == "XEQUE-MATE":
                print(f"\n--- FIM DE JOGO: XEQUE-MATE ---\nO jogador das {vencedor} venceu!")
            elif estado_final == "EMPATE_AFOGAMENTO":
                print(f"\n--- FIM DE JOGO: EMPATE (AFOGAMENTO) ---")
            elif estado_final == "EMPATE_50_LANCES":
                print(f"\n--- FIM DE JOGO: EMPATE (REGRA DOS 50 LANCES) ---")
            elif estado_final == "EMPATE_REPETICAO":
                print(f"\n--- FIM DE JOGO: EMPATE (REPETIÇÃO TRIPLA) ---")
            elif estado_final == "EMPATE_MATERIAL":
                print(f"\n--- FIM DE JOGO: EMPATE (MATERIAL INSUFICIENTE) ---")
            break
        elif esta_em_xeque(tabuleiro, turno_seguinte, historico):
            print(f"\n>>> O Rei {turno_seguinte.capitalize()} está em Xeque! <<<")


if __name__ == "__main__":
    jogar()