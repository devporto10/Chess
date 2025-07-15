# utils.py

import sys
import os


def resource_path(relative_path):
    """ Obtém o caminho absoluto para o recurso, funciona para dev e para o PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def converter_notacao_para_indices(notacao):
    """
    Converte uma notação de xadrez (ex: 'e2') para índices de matriz (ex: (6, 4)).
    """
    if not isinstance(notacao, str) or len(notacao) != 2:
        return None, None
    try:
        coluna_letra = notacao[0].lower()
        linha_num_str = notacao[1]
        if not ('a' <= coluna_letra <= 'h' and '1' <= linha_num_str <= '8'):
            return None, None
        coluna = ord(coluna_letra) - ord('a')
        linha = 8 - int(linha_num_str)
        return linha, coluna
    except (ValueError, IndexError):
        return None, None


def uci_para_movimento(movimento):
    """Converte nosso formato de movimento ((r,c),(r,c)) para uma string UCI 'e2e4'."""
    (r_ini, c_ini), (r_fim, c_fim) = movimento
    inicio_str = f"{chr(ord('a') + c_ini)}{8 - r_ini}"
    fim_str = f"{chr(ord('a') + c_fim)}{8 - r_fim}"
    return inicio_str + fim_str


def obter_notacao_lance(tabuleiro, movimento, alvo_en_passant_anterior, eh_xeque=False, eh_xeque_mate=False):
    """
    Converte um movimento para a notação de xadrez padrão (ex: Nf3, exd5, 0-0).
    """
    (r_ini, c_ini), (r_fim, c_fim) = movimento
    peca = tabuleiro[r_ini][c_ini]
    tipo_peca = peca.upper()

    # Roque
    if tipo_peca == 'K' and abs(c_ini - c_fim) == 2:
        return "0-0-0" if c_fim == 2 else "0-0"

    notacao = ""
    # Peça (exceto peão)
    if tipo_peca != 'P':
        notacao += tipo_peca

    # Captura
    peca_capturada = tabuleiro[r_fim][c_fim]
    is_en_passant = (tipo_peca == 'P' and (r_fim, c_fim) == alvo_en_passant_anterior)

    if peca_capturada != '.' or is_en_passant:
        if tipo_peca == 'P':
            notacao += chr(ord('a') + c_ini)  # Coluna de origem do peão
        notacao += 'x'

    # Casa de destino
    notacao += f"{chr(ord('a') + c_fim)}{8 - r_fim}"

    # Promoção (simplificado, sempre para Rainha)
    if tipo_peca == 'P' and (r_fim == 0 or r_fim == 7):
        notacao += '=Q'

    # Xeque ou Xeque-Mate
    if eh_xeque_mate:
        notacao += '#'
    elif eh_xeque:
        notacao += '+'

    return notacao