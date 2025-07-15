# processar_pgn.py (versão corrigida)

import chess
import chess.pgn
import os
from tabuleiro import criar_tabuleiro_inicial
from utils import converter_notacao_para_indices
# Importe a nova função!
from regras_jogo import gerar_hash_posicao, executar_movimento


def processar_arquivo_pgn(caminho_pgn_entrada, caminho_csv_saida, limite_jogos=100):
    """
    Lê um arquivo PGN, simula os jogos internamente para gerar hashes e
    salva os dados no formato (hash_da_posicao, movimento_uci) em um arquivo CSV.
    """
    if not os.path.exists(caminho_pgn_entrada):
        print(f"ERRO: Arquivo PGN não encontrado em '{caminho_pgn_entrada}'")
        return

    print(f"Iniciando processamento de '{caminho_pgn_entrada}'...")

    with open(caminho_pgn_entrada) as pgn_file, open(caminho_csv_saida, "w") as csv_file:
        csv_file.write("posicao,movimento\n")  # Escreve o cabeçalho

        jogos_processados = 0
        lances_totais = 0

        while jogos_processados < limite_jogos:
            jogo = chess.pgn.read_game(pgn_file)
            if jogo is None:
                break  # Fim do arquivo PGN

            # Usa o motor interno para simular a partida e manter o estado consistente
            estado_jogo = {
                'tabuleiro': criar_tabuleiro_inicial(), 'turno': 'branco',
                'historico_movimento': {'K': False, 'R_a1': False, 'R_h1': False, 'k': False, 'r_a8': False,
                                        'r_h8': False},
                'alvo_en_passant': None, 'contador_50_lances': 0, 'historico_posicoes': {}
            }
            # Adiciona o hash inicial ao histórico de posições
            hash_inicial = gerar_hash_posicao(estado_jogo['tabuleiro'], estado_jogo['turno'],
                                              estado_jogo['historico_movimento'], estado_jogo['alvo_en_passant'])
            estado_jogo['historico_posicoes'][hash_inicial] = 1

            for lance in jogo.mainline_moves():
                # Gera o hash ANTES de fazer o movimento
                posicao_hash = gerar_hash_posicao(
                    estado_jogo['tabuleiro'], estado_jogo['turno'],
                    estado_jogo['historico_movimento'], estado_jogo['alvo_en_passant']
                )

                # Converte o movimento da biblioteca chess para o nosso formato de tupla
                inicio_uci = lance.uci()[:2]
                fim_uci = lance.uci()[2:4]
                inicio_coords = converter_notacao_para_indices(inicio_uci)
                fim_coords = converter_notacao_para_indices(fim_uci)
                movimento_tupla = (inicio_coords, fim_coords)

                # Trata a promoção, que a lib chess informa separadamente
                if lance.promotion:
                    # Nossa função `executar_movimento` já promove para rainha por padrão,
                    # o que é suficiente para o processamento de dados.
                    pass

                # Salva no CSV
                csv_file.write(f'"{posicao_hash}","{movimento_tupla}"\n')
                lances_totais += 1

                # Executa o lance usando a função centralizada e ATUALIZA o estado do jogo
                estado_jogo = executar_movimento(estado_jogo, movimento_tupla)

            jogos_processados += 1
            if jogos_processados % 10 == 0:
                print(f"  ... {jogos_processados} jogos processados.")

    print(f"\nProcessamento concluído. {lances_totais} lances de mestre salvos em '{caminho_csv_saida}'.")


if __name__ == '__main__':
    # Exemplo de como usar o script
    processar_arquivo_pgn('partidas_mestres.pgn', 'dados_mestres.csv', limite_jogos=200)