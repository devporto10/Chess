# gui.py

import pygame
import sys
import copy
import os.path
import threading
import pygame_gui

from tabuleiro import criar_tabuleiro_inicial
from utils import converter_notacao_para_indices, uci_para_movimento, resource_path, obter_notacao_lance
from logica_movimento import eh_movimento_valido
from regras_jogo import esta_em_xeque, verificar_fim_de_jogo, gerar_hash_posicao, encontrar_posicao_rei
from ia import encontrar_melhor_movimento

try:
    from doppelganger import treinar_modelo, prever_movimento
except ImportError:
    # Definindo funções placeholder se a importação falhar
    def treinar_modelo(nome_modelo):
        print(
            f"AVISO: Módulo 'doppelganger' não encontrado. A função 'treinar_modelo' para {nome_modelo} não está disponível.")


    def prever_movimento(estado_jogo, nome_modelo):
        print(
            f"AVISO: Módulo 'doppelganger' não encontrado. A função 'prever_movimento' para {nome_modelo} não está disponível.")
        return None

try:
    from tutor_stockfish import Tutor, CAMINHO_STOCKFISH, encontrar_melhor_movimento_tutor
except ImportError:
    class Tutor:
        def __init__(self): pass

        def gerar_comentario_geral(self, *args, **kwargs): return {"feedback_texto": "Tutor indisponível."}

        def fechar_motor(self): pass


    def encontrar_melhor_movimento_tutor(e, t, d):
        return None


    CAMINHO_STOCKFISH = None

# --- Constantes, Cores e Fontes ---
LARGURA_BARRA_AVALIACAO = 20
LARGURA_TABULEIRO = 640
PAINEL_LATERAL = 320
LARGURA = LARGURA_TABULEIRO + PAINEL_LATERAL + LARGURA_BARRA_AVALIACAO
ALTURA = 750
LINHAS, COLUNAS = 8, 8
TAMANHO_CASA = LARGURA_TABULEIRO // COLUNAS
COR_CASA_CLARA = (240, 217, 181)
COR_CASA_ESCURA = (181, 136, 99)
COR_DESTAQUE_SELECAO = (135, 152, 106, 150)
COR_DESTAQUE_MOVIMENTO = (80, 150, 20, 120)
COR_DESTAQUE_XEQUE = (255, 0, 0, 100)
COR_DESTAQUE_ULTIMO_MOV = (255, 255, 0, 90)
COR_MENU_FUNDO = (30, 30, 30)
COR_BOTAO = (60, 60, 60);
COR_BOTAO_HOVER = (80, 80, 80)
COR_TEXTO = (220, 220, 220)
COR_FUNDO_PAINEL = (40, 37, 34)
COR_BALAO_TUTOR = (65, 62, 59)
COR_TEXTO_TUTOR = (255, 255, 255)
FONTE_TITULO, FONTE_BOTAO, FONTE_TUTOR, FONTE_HISTORICO, FONTE_ANALISE = None, None, None, None, None
IMAGENS_PECAS = {}
EFEITOS_SONOROS = {}
AVATAR_TUTOR = None


def carregar_assets():
    global AVATAR_TUTOR, FONTE_TITULO, FONTE_BOTAO, FONTE_TUTOR, FONTE_HISTORICO, FONTE_ANALISE
    try:
        caminho_fonte_regular = resource_path(os.path.join('assets', 'fonts', 'Roboto-Regular.ttf'))
        caminho_fonte_bold = resource_path(os.path.join('assets', 'fonts', 'Roboto-Bold.ttf'))
        FONTE_TITULO = pygame.font.Font(caminho_fonte_bold, 50)
        FONTE_BOTAO = pygame.font.Font(caminho_fonte_bold, 20)
        FONTE_TUTOR = pygame.font.Font(caminho_fonte_regular, 18)
        FONTE_HISTORICO = pygame.font.Font(caminho_fonte_regular, 16)
        FONTE_ANALISE = pygame.font.Font(caminho_fonte_bold, 28)
        pecas = ['P', 'R', 'N', 'B', 'Q', 'K']
        for peca in pecas:
            caminho_w = resource_path(os.path.join('assets', f'w{peca}.png'))
            caminho_b = resource_path(os.path.join('assets', f'b{peca}.png'))
            IMAGENS_PECAS[peca] = pygame.transform.scale(pygame.image.load(caminho_w).convert_alpha(),
                                                         (TAMANHO_CASA, TAMANHO_CASA))
            IMAGENS_PECAS[peca.lower()] = pygame.transform.scale(pygame.image.load(caminho_b).convert_alpha(),
                                                                 (TAMANHO_CASA, TAMANHO_CASA))
        caminho_avatar = resource_path(os.path.join('assets', 'tutor_avatar.png'))
        if os.path.exists(caminho_avatar): AVATAR_TUTOR = pygame.transform.scale(
            pygame.image.load(caminho_avatar).convert_alpha(), (60, 60))
        mapa_sons = {'move': 'move-self', 'capture': 'capture', 'check': 'check', 'game_end': 'game-end',
                     'promote': 'promote', 'castle': 'castle'}
        for evento, nome_arquivo in mapa_sons.items():
            caminho_arquivo = resource_path(os.path.join('assets', 'sounds', f'{nome_arquivo}.wav'))
            if os.path.exists(caminho_arquivo): EFEITOS_SONOROS[evento] = pygame.mixer.Sound(caminho_arquivo)
    except Exception as e:
        print(f"Erro ao carregar assets: {e}")


def wrap_text(text, font, max_width):
    lines = []
    words = text.split(' ')
    current_line = ""
    for word in words:
        sub_words = word.split('\n')
        for i, sub_word in enumerate(sub_words):
            test_line = f"{current_line} {sub_word}".strip()
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line);
                current_line = sub_word
            if i < len(sub_words) - 1: lines.append(current_line); current_line = ""
    lines.append(current_line)
    return lines


def desenhar_balao_de_dialogo(surface, color, rect, pointer_size=10, border_radius=15):
    pygame.draw.rect(surface, color, rect, border_radius=border_radius)
    pointer_y = rect.top + border_radius + 5
    p1 = (rect.left, pointer_y)
    p2 = (rect.left, pointer_y + pointer_size)
    p3 = (rect.left - pointer_size, pointer_y + pointer_size // 2)
    pygame.draw.polygon(surface, color, [p1, p2, p3])


class JogoGUI:
    def __init__(self, tela, modo_jogo, tempo_ia=5, dificuldade_tutor='dificil'):
        self.tela = tela
        self.modo_jogo = modo_jogo
        self.tempo_ia = tempo_ia
        self.dificuldade_tutor = dificuldade_tutor
        self.jogador_ia = None
        self.tabuleiro_invertido = False
        self.ia_usa_doppelganger = 'doppel' in self.modo_jogo
        self.ia_usa_mestre = 'mestre' in self.modo_jogo
        self.ia_usa_tutor_como_oponente = 'tutor_vs' in self.modo_jogo
        self.tutor = None
        if self.modo_jogo == 'tutor_analise' or self.ia_usa_tutor_como_oponente or 'tutor_vs' in self.modo_jogo:
            self.tutor = Tutor()
        if self.modo_jogo in ['hvp', 'doppel_p', 'mestre_p', 'tutor_vs_p']:
            self.jogador_ia = 'preto'  # CORREÇÃO SUTIL: Se Humano é Preto(p), a IA é Branca
            self.tabuleiro_invertido = True
        elif self.modo_jogo in ['hvb', 'doppel_b', 'mestre_b', 'tutor_vs_b']:
            self.jogador_ia = 'preto'

        self.manager_painel = pygame_gui.UIManager((LARGURA, ALTURA), 'theme.json')
        self.construir_painel_ui()
        self.resetar_jogo()

    def construir_painel_ui(self):
        self.painel_lateral = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((LARGURA_TABULEIRO + LARGURA_BARRA_AVALIACAO, 0), (PAINEL_LATERAL, ALTURA)),
            starting_height=-1,
            manager=self.manager_painel,
            object_id='#side_panel'
        )

        self.avatar_tutor_ui = pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect((10, 15), (60, 60)),
            image_surface=AVATAR_TUTOR if AVATAR_TUTOR else pygame.Surface((60, 60)),
            manager=self.manager_painel,
            container=self.painel_lateral)

        self.balao_tutor_ui = pygame_gui.elements.UITextBox(
            html_text="",
            relative_rect=pygame.Rect((80, 15), (PAINEL_LATERAL - 100, 120)),
            manager=self.manager_painel,
            container=self.painel_lateral)

        self.analise_box_ui = pygame_gui.elements.UITextBox(
            html_text="",
            relative_rect=pygame.Rect((10, 145), (PAINEL_LATERAL - 20, 90)),
            manager=self.manager_painel,
            container=self.painel_lateral,
            object_id="#analise_box")

        self.historico_ui = pygame_gui.elements.UITextBox(
            html_text="",
            relative_rect=pygame.Rect((10, 245), (PAINEL_LATERAL - 20, ALTURA - 325)),
            manager=self.manager_painel,
            container=self.painel_lateral)

        botoes_y_pos = ALTURA - 70
        self.botao_voltar_lance = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, botoes_y_pos), (140, 50)),
            text='Voltar Lance',
            manager=self.manager_painel,
            container=self.painel_lateral)

        self.botao_renderse = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((PAINEL_LATERAL - 150, botoes_y_pos), (140, 50)),
            text='Render-se',
            manager=self.manager_painel,
            container=self.painel_lateral)

    def atualizar_painel_ui(self):
        feedback = "Tutor está pensando..." if self.tutor_esta_pensando else self.estado_jogo.get('feedback_tutor', "")
        self.balao_tutor_ui.set_text(feedback)

        score = self.estado_jogo.get('analise_score')
        melhor_lance = self.estado_jogo.get('analise_melhor_lance', "N/A")
        texto_analise = ""
        if score is not None:
            cor_score = "#FFFFFF"
            if score > 0.1: cor_score = "#66FF66"  # Verde
            if score < -0.1: cor_score = "#FF6666"  # Vermelho
            texto_analise = (f"<font face='Roboto-Bold' size=6.5 color='{cor_score}'>{score:+.2f}</font><br>"
                             f"<font size=3.5>Melhor: <b>{melhor_lance}</b></font>")
        self.analise_box_ui.set_text(texto_analise)

        lances = self.estado_jogo['notacao_lances']
        texto_historico = "<b>Histórico de Lances</b><br>"
        for i in range(0, len(lances), 2):
            num_lance = (i // 2) + 1
            lance_branco = lances[i]
            lance_preto = lances[i + 1] if i + 1 < len(lances) else ""
            texto_historico += f"<font size=4>{num_lance}. {lance_branco}   {lance_preto}</font><br>"
        self.historico_ui.set_text(texto_historico)

        if self.estado_jogo['fim_de_jogo']:
            self.botao_voltar_lance.disable()
            self.botao_renderse.disable()
        else:
            self.botao_voltar_lance.enable()
            self.botao_renderse.enable()

    def resetar_jogo(self):
        self.estado_jogo = {'tabuleiro': criar_tabuleiro_inicial(), 'turno': 'branco',
                            'historico_movimento': {'K': False, 'R_a1': False, 'R_h1': False, 'k': False, 'r_a8': False,
                                                    'r_h8': False}, 'alvo_en_passant': None, 'contador_50_lances': 0,
                            'historico_posicoes': {}, 'pecas_brancas_capturadas': [], 'pecas_pretas_capturadas': [],
                            'ultimo_movimento': None, 'rei_em_xeque_pos': None, 'fim_de_jogo': None,
                            'feedback_tutor': "Vamos começar! Faça seu primeiro lance." if self.tutor else "",
                            'notacao_lances': [], 'analise_score': 0.0, 'analise_melhor_lance': "N/A"}
        hash_inicial = gerar_hash_posicao(self.estado_jogo['tabuleiro'], self.estado_jogo['turno'],
                                          self.estado_jogo['historico_movimento'], self.estado_jogo['alvo_en_passant'])
        self.estado_jogo['historico_posicoes'][hash_inicial] = 1
        self.peca_selecionada = None
        self.movimentos_validos = []
        self.historico_estados = [copy.deepcopy(self.estado_jogo)]
        self.lances_da_partida = []
        self.animando = False
        self.peca_animada = None
        self.pos_inicial_anim = (0, 0)
        self.pos_final_anim = (0, 0)
        self.progresso_anim = 0.0
        self.velocidade_anim = 0.15
        self.promovendo = False
        self.posicao_promocao = None
        self.opcoes_promocao_rects = []
        self.tutor_esta_pensando = False
        if self.tutor:
            self.solicitar_comentario_tutor_async(self.estado_jogo)
        self.atualizar_painel_ui()

    def _worker_obter_comentario(self, estado_jogo, estado_antes=None, lance_jogador_uci=None):
        analise_completa = self.tutor.gerar_comentario_geral(estado_jogo, estado_antes, lance_jogador_uci)
        if isinstance(analise_completa, dict):
            self.estado_jogo['feedback_tutor'] = analise_completa.get("feedback_texto", "")
            self.estado_jogo['analise_score'] = analise_completa.get("score")
            self.estado_jogo['analise_melhor_lance'] = analise_completa.get("melhor_lance")
        else:
            self.estado_jogo['feedback_tutor'] = analise_completa
            self.estado_jogo['analise_score'] = None
            self.estado_jogo['analise_melhor_lance'] = None
        self.tutor_esta_pensando = False

    def solicitar_comentario_tutor_async(self, estado_jogo, estado_antes=None, lance_jogador_uci=None):
        if not self.tutor or self.tutor_esta_pensando: return
        self.tutor_esta_pensando = True
        self.estado_jogo['analise_score'] = None
        self.estado_jogo['analise_melhor_lance'] = "Analisando..."
        thread_tutor = threading.Thread(target=self._worker_obter_comentario,
                                        args=(copy.deepcopy(estado_jogo), copy.deepcopy(estado_antes),
                                              lance_jogador_uci))
        thread_tutor.start()

    def desfazer_lance(self):
        if self.estado_jogo['fim_de_jogo']: return
        num_desfazer = 2 if self.jogador_ia and len(self.historico_estados) > 2 else 1
        if len(self.historico_estados) <= num_desfazer: return
        for _ in range(num_desfazer):
            self.historico_estados.pop()
            if self.lances_da_partida: self.lances_da_partida.pop()
        self.estado_jogo = copy.deepcopy(self.historico_estados[-1])
        self.peca_selecionada = None
        self.movimentos_validos = []
        if 'move' in EFEITOS_SONOROS: EFEITOS_SONOROS['move'].play()
        if self.tutor:
            self.solicitar_comentario_tutor_async(self.estado_jogo)

    def converter_coords_para_tela(self, r, c):
        return (7 - r, 7 - c) if self.tabuleiro_invertido else (r, c)

    def desenhar_barra_avaliacao(self):
        if self.tutor is None: return

        score_value = self.estado_jogo.get('analise_score')
        if score_value is None:
            score_value = 0.0

        max_eval = 8.0
        clamped_eval = max(-max_eval, min(max_eval, score_value))

        white_percent = 0.5 + (clamped_eval / (2 * max_eval))

        altura_tabuleiro = LARGURA_TABULEIRO
        bar_rect = pygame.Rect(0, 0, LARGURA_BARRA_AVALIACAO, altura_tabuleiro)

        altura_brancas = altura_tabuleiro * white_percent
        altura_pretas = altura_tabuleiro - altura_brancas

        rect_pretas = pygame.Rect(bar_rect.left, bar_rect.top, bar_rect.width, altura_pretas)
        rect_brancas = pygame.Rect(bar_rect.left, bar_rect.top + altura_pretas, bar_rect.width, altura_brancas)

        pygame.draw.rect(self.tela, (20, 20, 20), rect_pretas)
        pygame.draw.rect(self.tela, (230, 230, 230), rect_brancas)

    def desenhar_estado(self):
        self.tela.fill(COR_FUNDO_PAINEL)
        self.desenhar_barra_avaliacao()

        offset_x = LARGURA_BARRA_AVALIACAO

        tabuleiro_surface = self.tela.subsurface(pygame.Rect(offset_x, 0, LARGURA_TABULEIRO, LARGURA_TABULEIRO))

        tabuleiro = self.estado_jogo['tabuleiro']
        for r_logica in range(LINHAS):
            for c_logica in range(COLUNAS):
                r_tela, c_tela = self.converter_coords_para_tela(r_logica, c_logica)
                cor = COR_CASA_CLARA if (r_logica + c_logica) % 2 == 0 else COR_CASA_ESCURA
                pygame.draw.rect(tabuleiro_surface, cor,
                                 (c_tela * TAMANHO_CASA, r_tela * TAMANHO_CASA, TAMANHO_CASA, TAMANHO_CASA))
        if self.estado_jogo['ultimo_movimento']:
            r_ini_tela, c_ini_tela = self.converter_coords_para_tela(self.estado_jogo['ultimo_movimento'][0][0],
                                                                     self.estado_jogo['ultimo_movimento'][0][1]);
            r_fim_tela, c_fim_tela = self.converter_coords_para_tela(self.estado_jogo['ultimo_movimento'][1][0],
                                                                     self.estado_jogo['ultimo_movimento'][1][1])
            s = pygame.Surface((TAMANHO_CASA, TAMANHO_CASA), pygame.SRCALPHA);
            s.fill(COR_DESTAQUE_ULTIMO_MOV)
            tabuleiro_surface.blit(s, (c_ini_tela * TAMANHO_CASA, r_ini_tela * TAMANHO_CASA));
            tabuleiro_surface.blit(s, (c_fim_tela * TAMANHO_CASA, r_fim_tela * TAMANHO_CASA))
        if self.peca_selecionada:
            r_sel_tela, c_sel_tela = self.converter_coords_para_tela(self.peca_selecionada[0], self.peca_selecionada[1])
            s_sel = pygame.Surface((TAMANHO_CASA, TAMANHO_CASA), pygame.SRCALPHA);
            s_sel.fill(COR_DESTAQUE_SELECAO)
            tabuleiro_surface.blit(s_sel, (c_sel_tela * TAMANHO_CASA, r_sel_tela * TAMANHO_CASA))
            for mov in self.movimentos_validos:
                r_mov_tela, c_mov_tela = self.converter_coords_para_tela(mov[0], mov[1])
                s_mov = pygame.Surface((TAMANHO_CASA, TAMANHO_CASA), pygame.SRCALPHA)
                pygame.draw.circle(s_mov, COR_DESTAQUE_MOVIMENTO, (TAMANHO_CASA // 2, TAMANHO_CASA // 2),
                                   TAMANHO_CASA // 4)
                tabuleiro_surface.blit(s_mov, (c_mov_tela * TAMANHO_CASA, r_mov_tela * TAMANHO_CASA))
        if self.estado_jogo['rei_em_xeque_pos']:
            r_xeque_tela, c_xeque_tela = self.converter_coords_para_tela(self.estado_jogo['rei_em_xeque_pos'][0],
                                                                         self.estado_jogo['rei_em_xeque_pos'][1])
            s_xeque = pygame.Surface((TAMANHO_CASA, TAMANHO_CASA), pygame.SRCALPHA);
            s_xeque.fill(COR_DESTAQUE_XEQUE)
            tabuleiro_surface.blit(s_xeque, (c_xeque_tela * TAMANHO_CASA, r_xeque_tela * TAMANHO_CASA))
        for r_logica in range(LINHAS):
            for c_logica in range(COLUNAS):
                if self.animando and self.estado_jogo['ultimo_movimento'] and (r_logica, c_logica) == \
                        self.estado_jogo['ultimo_movimento'][1]: continue
                peca = tabuleiro[r_logica][c_logica]
                if peca != '.':
                    r_tela, c_tela = self.converter_coords_para_tela(r_logica, c_logica)
                    tabuleiro_surface.blit(IMAGENS_PECAS[peca], (c_tela * TAMANHO_CASA, r_tela * TAMANHO_CASA))
        if self.animando:
            x_atual = self.pos_inicial_anim[0] + (
                    self.pos_final_anim[0] - self.pos_inicial_anim[0]) * self.progresso_anim
            y_atual = self.pos_inicial_anim[1] + (
                    self.pos_final_anim[1] - self.pos_inicial_anim[1]) * self.progresso_anim
            tabuleiro_surface.blit(self.peca_animada, (x_atual, y_atual))
        if self.estado_jogo['fim_de_jogo']:
            fonte = pygame.font.Font(None, 74)
            texto_surface = fonte.render(self.estado_jogo['fim_de_jogo'], True, (200, 20, 20))
            texto_rect = texto_surface.get_rect(center=(LARGURA_TABULEIRO / 2, LARGURA_TABULEIRO / 2));
            fundo_rect = texto_rect.inflate(20, 20)
            fundo_surface = pygame.Surface(fundo_rect.size, pygame.SRCALPHA);
            fundo_surface.fill((255, 255, 255, 220))
            tabuleiro_surface.blit(fundo_surface, fundo_rect);
            tabuleiro_surface.blit(texto_surface, texto_rect)
        if self.promovendo:
            self.desenhar_menu_promocao(offset_x)

    def desenhar_menu_promocao(self, offset_x=0):
        r_tela, c_tela = self.converter_coords_para_tela(self.posicao_promocao[0], self.posicao_promocao[1])
        x_base = c_tela * TAMANHO_CASA + offset_x;
        y_base = r_tela * TAMANHO_CASA;
        fundo_menu_altura = TAMANHO_CASA * 4
        y_menu = y_base if r_tela < 4 else y_base - (fundo_menu_altura - TAMANHO_CASA)
        fundo = pygame.Surface((TAMANHO_CASA, fundo_menu_altura), pygame.SRCALPHA);
        fundo.fill((20, 20, 20, 220));
        self.tela.blit(fundo, (x_base, y_menu));
        self.opcoes_promocao_rects.clear()
        for i, p_char in enumerate(['q', 'r', 'b', 'n']):
            peca_real = p_char.upper() if self.estado_jogo['turno'] == 'branco' else p_char
            y_offset = i * TAMANHO_CASA if r_tela < 4 else (3 - i) * TAMANHO_CASA
            rect = pygame.Rect(x_base, y_menu + y_offset, TAMANHO_CASA, TAMANHO_CASA)
            self.tela.blit(IMAGENS_PECAS[peca_real], rect.topleft);
            self.opcoes_promocao_rects.append((rect, peca_real))

    def selecionar(self, linha, coluna):
        if self.animando or self.promovendo or coluna >= COLUNAS or self.estado_jogo['fim_de_jogo']: return
        if self.peca_selecionada:
            movimento = (self.peca_selecionada, (linha, coluna))
            if movimento[1] in self.movimentos_validos:
                self.executar_movimento(movimento)
            self.peca_selecionada, self.movimentos_validos = None, []
            return
        peca = self.estado_jogo['tabuleiro'][linha][coluna]
        turno_atual = self.estado_jogo['turno']
        if peca != '.' and (
                (turno_atual == 'branco' and peca.isupper()) or (turno_atual == 'preto' and peca.islower())):
            self.peca_selecionada = (linha, coluna)
            self.movimentos_validos = self.calcular_movimentos_validos_para_peca((linha, coluna))

    def calcular_movimentos_validos_para_peca(self, pos_peca):
        movimentos = []
        estado = self.estado_jogo
        for r in range(LINHAS):
            for c in range(COLUNAS):
                if eh_movimento_valido(estado['tabuleiro'], pos_peca, (r, c), estado['turno'],
                                       estado['historico_movimento'], estado['alvo_en_passant']):
                    tabuleiro_simulado = copy.deepcopy(estado['tabuleiro'])
                    peca_movida = tabuleiro_simulado[pos_peca[0]][pos_peca[1]]
                    tabuleiro_simulado[pos_peca[0]][pos_peca[1]] = '.'
                    tabuleiro_simulado[r][c] = peca_movida
                    if not esta_em_xeque(tabuleiro_simulado, estado['turno'], estado['historico_movimento']):
                        movimentos.append((r, c))
        return movimentos

    def executar_movimento(self, movimento):
        self.lances_da_partida.append(movimento)
        estado_antes_movimento = copy.deepcopy(self.estado_jogo)
        # self.historico_estados.append(estado_antes_movimento) # Movido para dentro de finalizar_turno

        linha_inicio, col_inicio = movimento[0]
        linha_fim, col_fim = movimento[1]
        self.estado_jogo['ultimo_movimento'] = ((linha_inicio, col_inicio), (linha_fim, col_fim))

        # Animação
        r_ini_tela, c_ini_tela = self.converter_coords_para_tela(linha_inicio, col_inicio)
        r_fim_tela, c_fim_tela = self.converter_coords_para_tela(linha_fim, col_fim)
        self.animando = True
        self.peca_animada = IMAGENS_PECAS[self.estado_jogo['tabuleiro'][linha_inicio][col_inicio]]
        self.pos_inicial_anim = (c_ini_tela * TAMANHO_CASA, r_ini_tela * TAMANHO_CASA)
        self.pos_final_anim = (c_fim_tela * TAMANHO_CASA, r_fim_tela * TAMANHO_CASA)
        self.progresso_anim = 0.0

        # <--- MUDANÇA PRINCIPAL: LÓGICA DE PROMOÇÃO ---
        foi_promocao = estado_antes_movimento['tabuleiro'][linha_inicio][col_inicio].lower() == 'p' and (
                linha_fim == 0 or linha_fim == 7)

        if foi_promocao:
            # Se a IA está promovendo, faz automaticamente para Rainha
            if self.turno_da_ia():
                peca_promovida = 'Q' if estado_antes_movimento['turno'] == 'branco' else 'q'
                self.estado_jogo['tabuleiro'][linha_inicio][col_inicio] = '.'
                self.estado_jogo['tabuleiro'][linha_fim][col_fim] = peca_promovida
                # O turno é finalizado, passando a informação que foi uma promoção
                self.finalizar_turno(movimento, estado_antes_movimento, foi_promocao_final=True)
            # Se for humano, mostra o menu
            else:
                self.promovendo = True
                self.posicao_promocao = (linha_fim, col_fim)
                # Remove o peão temporariamente para a animação
                self.estado_jogo['tabuleiro'][linha_inicio][col_inicio] = '.'
                # Não chama finalizar_turno ainda, espera a escolha do jogador
        else:
            # Se não for promoção, finaliza o turno normalmente
            self.finalizar_turno(movimento, estado_antes_movimento)
        # <--- FIM DA MUDANÇA PRINCIPAL ---

    def finalizar_promocao(self, peca_escolhida):
        self.promovendo = False
        r_fim, c_fim = self.posicao_promocao
        self.estado_jogo['tabuleiro'][r_fim][c_fim] = peca_escolhida
        estado_antes_final = self.historico_estados[-1]  # Pega o estado antes do peão mover
        self.finalizar_turno(self.estado_jogo['ultimo_movimento'], estado_antes_final, foi_promocao_final=True)

    def finalizar_turno(self, movimento, estado_antes, foi_promocao_final=False):
        # Apenas adiciona ao histórico o estado ANTES do movimento que está sendo finalizado
        self.historico_estados.append(estado_antes)

        turno_do_movimento = estado_antes['turno']
        tabuleiro = self.estado_jogo['tabuleiro']
        historico = self.estado_jogo['historico_movimento']
        linha_inicio, col_inicio = movimento[0]
        linha_fim, col_fim = movimento[1]
        peca = estado_antes['tabuleiro'][linha_inicio][col_inicio]
        alvo_ep = estado_antes['alvo_en_passant']
        foi_captura_en_passant = peca.lower() == 'p' and (linha_fim, col_fim) == alvo_ep

        # A movimentação da peça só acontece aqui para movimentos normais
        if not foi_promocao_final:
            peca_capturada_antes = estado_antes['tabuleiro'][linha_fim][col_fim]
            if foi_captura_en_passant:
                peca_capturada = tabuleiro[linha_inicio][col_fim]
                self.estado_jogo[
                    'pecas_pretas_capturadas' if peca_capturada.islower() else 'pecas_brancas_capturadas'].append(
                    peca_capturada)
                tabuleiro[linha_inicio][col_fim] = '.'
            elif peca_capturada_antes != '.':
                self.estado_jogo[
                    'pecas_pretas_capturadas' if peca_capturada_antes.islower() else 'pecas_brancas_capturadas'].append(
                    peca_capturada_antes)
            tabuleiro[linha_inicio][col_inicio] = '.'
            tabuleiro[linha_fim][col_fim] = peca

        foi_captura = estado_antes['tabuleiro'][linha_fim][col_fim] != '.' or foi_captura_en_passant
        foi_roque = peca.lower() == 'k' and abs(col_inicio - col_fim) == 2
        if foi_roque:
            if col_fim == 6:
                torre = tabuleiro[linha_fim][7];
                tabuleiro[linha_fim][7] = '.';
                tabuleiro[linha_fim][5] = torre
            elif col_fim == 2:
                torre = tabuleiro[linha_fim][0];
                tabuleiro[linha_fim][0] = '.';
                tabuleiro[linha_fim][3] = torre

        if peca.lower() == 'p' or foi_captura:
            self.estado_jogo['contador_50_lances'] = 0
        else:
            self.estado_jogo['contador_50_lances'] += 1

        self.estado_jogo['alvo_en_passant'] = ((linha_inicio + linha_fim) // 2,
                                               col_inicio) if peca.lower() == 'p' and abs(
            linha_inicio - linha_fim) == 2 else None

        # Atualiza histórico de movimentos para roque
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

        foi_lance_humano = (self.jogador_ia is None or turno_do_movimento != self.jogador_ia)
        turno_seguinte_logico = 'preto' if turno_do_movimento == 'branco' else 'branco'
        eh_xeque_agora = esta_em_xeque(tabuleiro, turno_seguinte_logico, historico)
        estado_final_check = verificar_fim_de_jogo(tabuleiro, turno_seguinte_logico, historico,
                                                   self.estado_jogo['contador_50_lances'],
                                                   self.estado_jogo['historico_posicoes'],
                                                   self.estado_jogo['alvo_en_passant'])

        notacao = obter_notacao_lance(estado_antes['tabuleiro'], movimento, alvo_ep, eh_xeque_agora,
                                      (estado_final_check == "XEQUE-MATE"))

        if foi_promocao_final:
            peca_promovida_char = self.estado_jogo['tabuleiro'][linha_fim][col_fim].upper()
            notacao += f"={peca_promovida_char}"  # <--- MUDANÇA: notação de promoção

        self.estado_jogo['notacao_lances'].append(notacao)
        self.estado_jogo['turno'] = turno_seguinte_logico
        if self.tutor and foi_lance_humano:
            lance_uci = uci_para_movimento(movimento)
            self.solicitar_comentario_tutor_async(self.estado_jogo, estado_antes, lance_uci)

        hash_atual = gerar_hash_posicao(tabuleiro, self.estado_jogo['turno'], historico,
                                        self.estado_jogo['alvo_en_passant'])
        self.estado_jogo['historico_posicoes'][hash_atual] = self.estado_jogo['historico_posicoes'].get(hash_atual,
                                                                                                        0) + 1
        estado_final = verificar_fim_de_jogo(tabuleiro, self.estado_jogo['turno'], historico,
                                             self.estado_jogo['contador_50_lances'],
                                             self.estado_jogo['historico_posicoes'],
                                             self.estado_jogo['alvo_en_passant'])
        self.estado_jogo['rei_em_xeque_pos'] = None
        if estado_final:
            self.estado_jogo['fim_de_jogo'] = f"Empate! ({estado_final.split('_')[-1].title()})"
            if estado_final == "XEQUE-MATE": self.estado_jogo[
                'fim_de_jogo'] = f"Xeque-Mate! {'Pretas' if self.estado_jogo['turno'] == 'branco' else 'Brancas'} vencem."
            if 'game_end' in EFEITOS_SONOROS: EFEITOS_SONOROS['game_end'].play()
        elif esta_em_xeque(tabuleiro, self.estado_jogo['turno'], historico):
            self.estado_jogo['rei_em_xeque_pos'] = encontrar_posicao_rei(tabuleiro, self.estado_jogo['turno'])
            if 'check' in EFEITOS_SONOROS: EFEITOS_SONOROS['check'].play()
        elif foi_roque or foi_promocao_final:
            if foi_roque and 'castle' in EFEITOS_SONOROS: EFEITOS_SONOROS['castle'].play()
            if foi_promocao_final and 'promote' in EFEITOS_SONOROS: EFEITOS_SONOROS['promote'].play()
        elif foi_captura:
            if 'capture' in EFEITOS_SONOROS: EFEITOS_SONOROS['capture'].play()
        else:
            if 'move' in EFEITOS_SONOROS: EFEITOS_SONOROS['move'].play()

    def fazer_jogada_ia(self):
        if not self.turno_da_ia() or self.estado_jogo['fim_de_jogo']: return
        pygame.time.wait(100)
        melhor_movimento = None
        if self.ia_usa_tutor_como_oponente:
            melhor_movimento = encontrar_melhor_movimento_tutor(self.estado_jogo, self.tempo_ia, self.dificuldade_tutor)
        elif self.ia_usa_doppelganger:
            melhor_movimento = prever_movimento(self.estado_jogo, 'doppelganger')
        elif self.ia_usa_mestre:
            melhor_movimento = prever_movimento(self.estado_jogo, 'mestre')
        else:
            melhor_movimento = encontrar_melhor_movimento(self.estado_jogo, self.tempo_ia)

        if melhor_movimento:
            self.peca_selecionada = None
            self.movimentos_validos = []
            self.executar_movimento(melhor_movimento)
            if self.tutor and not self.estado_jogo['fim_de_jogo']:
                self.solicitar_comentario_tutor_async(self.estado_jogo)
        else:
            # Se a IA não retornou um movimento (pode ser fim de jogo ou erro), não faz nada.
            # O sistema de verificação de fim de jogo já deve ter capturado isso.
            print("AVISO: IA não retornou um movimento.")

    def render_se(self):
        if self.estado_jogo['fim_de_jogo']: return
        turno_atual = self.estado_jogo['turno']
        perdedor = "Brancas" if turno_atual == 'branco' else "Pretas"
        vencedor = "Pretas" if turno_atual == 'branco' else "Brancas"
        self.estado_jogo['fim_de_jogo'] = f"{perdedor} se renderam. {vencedor} vencem!"
        if 'game_end' in EFEITOS_SONOROS: EFEITOS_SONOROS['game_end'].play()

    def turno_da_ia(self):
        return self.jogador_ia is not None and self.jogador_ia == self.estado_jogo['turno']


class RevisaoGUI:
    def __init__(self, t, l, h):
        self.tela = t;
        self.lances_da_partida = l;
        self.historico_estados = h;
        self.indice_lance_atual = -1;
        self.tutor = Tutor();
        self.feedback_atual = "Use as setas para revisar.";
        self.estado_jogo_exibido = \
            self.historico_estados[0];
        y = LARGURA_TABULEIRO + 45;
        w = 50;
        s = 15;
        x = LARGURA_TABULEIRO + LARGURA_BARRA_AVALIACAO + (
                PAINEL_LATERAL - (4 * w + 3 * s)) / 2;
        self.botoes_revisao = {'inicio': pygame.Rect(x, y, w, 35),
                               'anterior': pygame.Rect(x + w + s, y,
                                                       w, 35),
                               'proximo': pygame.Rect(
                                   x + 2 * (w + s), y, w, 35),
                               'fim': pygame.Rect(x + 3 * (w + s), y,
                                                  w,
                                                  35)};
        self.analisar_lance_atual()

    def navegar_lance(self, d):
        n = self.indice_lance_atual + d;
        self.indice_lance_atual = n if -1 <= n < len(
            self.lances_da_partida) else self.indice_lance_atual;
        self.analisar_lance_atual()

    def ir_para_inicio(self):
        self.indice_lance_atual = -1;
        self.analisar_lance_atual()

    def ir_para_fim(self):
        self.indice_lance_atual = len(
            self.lances_da_partida) - 1 if self.lances_da_partida else -1;
        self.analisar_lance_atual()

    def analisar_lance_atual(self):
        if self.indice_lance_atual == -1: self.estado_jogo_exibido = self.historico_estados[
            0]; self.feedback_atual = "Posição inicial."; return
        e_a = self.historico_estados[self.indice_lance_atual];
        e_d = self.historico_estados[self.indice_lance_atual + 1];
        l_f = self.lances_da_partida[self.indice_lance_atual];
        self.estado_jogo_exibido = e_d;
        l_u = uci_para_movimento(l_f);
        self.feedback_atual = "Analisando...";
        self.desenhar_revisao();
        pygame.display.flip();
        analise = self.tutor.gerar_comentario_geral(e_d, e_a, l_u)
        if isinstance(analise, dict):
            self.feedback_atual = f"{analise['feedback_texto']}\nScore: {analise['score']:.2f}\nMelhor: {analise['melhor_lance']}"
        else:
            self.feedback_atual = analise

    def desenhar_revisao(self):
        self.tela.fill(COR_FUNDO_PAINEL);
        offset_x_painel = LARGURA_TABULEIRO + LARGURA_BARRA_AVALIACAO
        pygame.draw.rect(self.tela, COR_FUNDO_PAINEL, (offset_x_painel, 0, PAINEL_LATERAL, ALTURA));
        y_atual = 15
        if self.tutor and self.feedback_atual:
            avatar_x = offset_x_painel + 15
            if AVATAR_TUTOR:
                balao_inner_width = PAINEL_LATERAL - (avatar_x - offset_x_painel) - AVATAR_TUTOR.get_width() - 45
                balao_x = avatar_x + AVATAR_TUTOR.get_width() + 10
            else:
                balao_inner_width = PAINEL_LATERAL - 45
                balao_x = avatar_x

            linhas_de_texto = wrap_text(self.feedback_atual, FONTE_TUTOR, balao_inner_width)
            altura_texto = len(linhas_de_texto) * FONTE_TUTOR.get_linesize()
            balao_rect = pygame.Rect(balao_x, y_atual, balao_inner_width + 20, altura_texto + 20)
            if AVATAR_TUTOR: self.tela.blit(AVATAR_TUTOR, (avatar_x, y_atual))
            desenhar_balao_de_dialogo(self.tela, COR_BALAO_TUTOR, balao_rect)
            for i, linha in enumerate(linhas_de_texto):
                self.tela.blit(FONTE_TUTOR.render(linha, True, COR_TEXTO_TUTOR),
                               (balao_rect.x + 10, balao_rect.y + 10 + i * FONTE_TUTOR.get_linesize()))
            y_atual += balao_rect.height + 30
        self.tela.blit(FONTE_BOTAO.render("Lances:", True, COR_TEXTO), (offset_x_painel + 15, y_atual));
        y_atual += 35
        x_num = offset_x_painel + 20;
        x_branco = offset_x_painel + 70;
        x_preto = offset_x_painel + 190
        notacoes = self.estado_jogo_exibido['notacao_lances']
        for i in range(0, len(notacoes), 2):
            if y_atual > ALTURA - 120: break
            move_num = (i // 2) + 1
            cor_linha = (255, 255, 0) if i == self.indice_lance_atual or i + 1 == self.indice_lance_atual else COR_TEXTO
            self.tela.blit(FONTE_HISTORICO.render(f"{move_num}.", True, cor_linha), (x_num, y_atual))
            self.tela.blit(FONTE_HISTORICO.render(notacoes[i], True, cor_linha), (x_branco, y_atual))
            if i + 1 < len(notacoes): self.tela.blit(FONTE_HISTORICO.render(notacoes[i + 1], True, cor_linha),
                                                     (x_preto, y_atual))
            y_atual += 25
        for nome, rect in self.botoes_revisao.items():
            pygame.draw.rect(self.tela, COR_BOTAO, rect, border_radius=5);
            simbolos = {'inicio': '<<', 'anterior': '<', 'proximo': '>', 'fim': '>>'};
            t_s = FONTE_BOTAO.render(simbolos[nome], True, COR_TEXTO);
            self.tela.blit(t_s, t_s.get_rect(center=rect.center))

        offset_x_tabuleiro = LARGURA_BARRA_AVALIACAO
        tabuleiro_surface = self.tela.subsurface(
            pygame.Rect(offset_x_tabuleiro, 0, LARGURA_TABULEIRO, LARGURA_TABULEIRO))
        tabuleiro = self.estado_jogo_exibido['tabuleiro']
        for r in range(LINHAS):
            for c in range(COLUNAS): cor = COR_CASA_CLARA if (r + c) % 2 == 0 else COR_CASA_ESCURA; pygame.draw.rect(
                tabuleiro_surface, cor, (c * TAMANHO_CASA, r * TAMANHO_CASA, TAMANHO_CASA, TAMANHO_CASA))
        if self.indice_lance_atual >= 0: m = self.lances_da_partida[self.indice_lance_atual]; r_i, c_i = m[
            0]; r_f, c_f = m[1]; s = pygame.Surface((TAMANHO_CASA, TAMANHO_CASA), pygame.SRCALPHA); s.fill(
            COR_DESTAQUE_ULTIMO_MOV); tabuleiro_surface.blit(s, (c_i * TAMANHO_CASA,
                                                                 r_i * TAMANHO_CASA)); tabuleiro_surface.blit(s,
                                                                                                              (c_f * TAMANHO_CASA,
                                                                                                               r_f * TAMANHO_CASA))
        for r in range(LINHAS):
            for c in range(COLUNAS):
                p = tabuleiro[r][c]
                if p != '.':
                    tabuleiro_surface.blit(IMAGENS_PECAS[p], (c * TAMANHO_CASA, r * TAMANHO_CASA))

    def fechar(self):
        if self.tutor: self.tutor.fechar_motor()


def loop_principal():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Xadrez em Python")
    carregar_assets()
    clock = pygame.time.Clock()

    manager = pygame_gui.UIManager((LARGURA, ALTURA), 'theme.json')

    y_pos = 140;
    y_inc = 55;
    largura_botao = 280;
    espaco_botao = 20
    x_pos1 = (LARGURA - (2 * largura_botao + espaco_botao)) / 2
    x_pos2 = x_pos1 + largura_botao + espaco_botao

    pygame_gui.elements.UILabel(relative_rect=pygame.Rect((0, 20), (LARGURA, 100)),
                                text='Xadrez Python',
                                manager=manager,
                                object_id='@title_text')

    botoes_gui = {}
    botoes_gui["Humano vs Humano"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(x_pos1, y_pos, largura_botao * 2 + espaco_botao, 50), text='Humano vs Humano',
        manager=manager)
    botoes_gui["Jogar de Brancas (vs IA)"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(x_pos1, y_pos + y_inc, largura_botao, 50), text='Jogar de Brancas (vs IA)',
        manager=manager)
    botoes_gui["Jogar de Pretas (vs IA)"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(x_pos2, y_pos + y_inc, largura_botao, 50), text='Jogar de Pretas (vs IA)',
        manager=manager)
    botoes_gui["vs Doppelgänger (Brancas)"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(x_pos1, y_pos + 2 * y_inc, largura_botao, 50), text='vs Doppelgänger (Brancas)',
        manager=manager)
    botoes_gui["vs Doppelgänger (Pretas)"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(x_pos2, y_pos + 2 * y_inc, largura_botao, 50), text='vs Doppelgänger (Pretas)',
        manager=manager)
    botoes_gui["vs Mestre IA (Brancas)"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(x_pos1, y_pos + 3 * y_inc, largura_botao, 50), text='vs Mestre IA (Brancas)',
        manager=manager)
    botoes_gui["vs Mestre IA (Pretas)"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(x_pos2, y_pos + 3 * y_inc, largura_botao, 50), text='vs Mestre IA (Pretas)',
        manager=manager)
    botoes_gui["vs Tutor (Fácil)"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(x_pos1, y_pos + 4 * y_inc, largura_botao, 50), text='vs Tutor (Fácil)',
        manager=manager)
    botoes_gui["Jogar de Pretas (Fácil)"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(x_pos2, y_pos + 4 * y_inc, largura_botao, 50), text='Jogar de Pretas (Fácil)',
        manager=manager)
    botoes_gui["vs Tutor (Médio)"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(x_pos1, y_pos + 5 * y_inc, largura_botao, 50), text='vs Tutor (Médio)',
        manager=manager)
    botoes_gui["Jogar de Pretas (Médio)"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(x_pos2, y_pos + 5 * y_inc, largura_botao, 50), text='Jogar de Pretas (Médio)',
        manager=manager)
    botoes_gui["vs Tutor (Difícil)"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(x_pos1, y_pos + 6 * y_inc, largura_botao, 50), text='vs Tutor (Difícil)',
        manager=manager)
    botoes_gui["Jogar de Pretas (Difícil)"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(x_pos2, y_pos + 6 * y_inc, largura_botao, 50), text='Jogar de Pretas (Difícil)',
        manager=manager)
    botoes_gui["Treinar Doppelgänger"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(x_pos1, y_pos + 7 * y_inc + 10, largura_botao, 50), text='Treinar Doppelgänger',
        manager=manager)
    botoes_gui["Treinar Mestre IA"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(x_pos2, y_pos + 7 * y_inc + 10, largura_botao, 50), text='Treinar Mestre IA',
        manager=manager)
    botoes_gui["Modo Análise (Tutor)"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(x_pos1, y_pos + 8 * y_inc + 20, largura_botao * 2 + espaco_botao, 50),
        text='Modo Análise (Tutor)', manager=manager)
    botoes_gui["Sair"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(x_pos1, y_pos + 9 * y_inc + 30, largura_botao * 2 + espaco_botao, 50), text='Sair',
        manager=manager)

    def atualizar_estado_botoes():
        try:
            if not os.path.exists(resource_path('modelo_doppelganger.pkl')):
                botoes_gui["vs Doppelgänger (Brancas)"].disable();
                botoes_gui["vs Doppelgänger (Pretas)"].disable()
            if not os.path.exists(resource_path('modelo_mestre.pkl')):
                botoes_gui["vs Mestre IA (Brancas)"].disable();
                botoes_gui["vs Mestre IA (Pretas)"].disable()
            if not CAMINHO_STOCKFISH:
                for nome, botao in botoes_gui.items():
                    if 'Tutor' in nome or 'Análise' in nome:
                        botao.disable()
            if not os.path.exists(resource_path('dados_treino.csv')):
                botoes_gui["Treinar Doppelgänger"].disable()
            if not os.path.exists(resource_path('dados_mestres.csv')):
                botoes_gui["Treinar Mestre IA"].disable()
        except Exception as e:
            print(f"Erro ao atualizar estado dos botões: {e}")

    atualizar_estado_botoes()
    estado_app = 'MENU'
    jogo = None
    revisao = None
    rodando = True

    while rodando:
        time_delta = clock.tick(60) / 1000.0
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

            if estado_app == 'MENU':
                manager.process_events(evento)
                if evento.type == pygame_gui.UI_BUTTON_PRESSED:
                    btn_clicado = evento.ui_element
                    nome_botao = btn_clicado.text if hasattr(btn_clicado, 'text') else ''

                    if nome_botao == "Sair":
                        rodando = False
                    else:
                        modo_jogo_selecionado = None
                        if nome_botao == "Humano vs Humano":
                            modo_jogo_selecionado = 'hvh'
                        elif nome_botao == "Jogar de Brancas (vs IA)":
                            modo_jogo_selecionado = 'hvb'
                            jogo = JogoGUI(tela, modo_jogo_selecionado, 5)
                        elif nome_botao == "Jogar de Pretas (vs IA)":
                            modo_jogo_selecionado = 'hvp'
                            jogo = JogoGUI(tela, modo_jogo_selecionado, 5)
                        elif nome_botao == "vs Doppelgänger (Brancas)":
                            modo_jogo_selecionado = 'doppel_b'
                            jogo = JogoGUI(tela, modo_jogo_selecionado)
                        elif nome_botao == "vs Doppelgänger (Pretas)":
                            modo_jogo_selecionado = 'doppel_p'
                            jogo = JogoGUI(tela, modo_jogo_selecionado)
                        elif nome_botao == "vs Mestre IA (Brancas)":
                            modo_jogo_selecionado = 'mestre_b'
                            jogo = JogoGUI(tela, modo_jogo_selecionado)
                        elif nome_botao == "vs Mestre IA (Pretas)":
                            modo_jogo_selecionado = 'mestre_p'
                            jogo = JogoGUI(tela, modo_jogo_selecionado)
                        elif nome_botao == "vs Tutor (Fácil)":
                            jogo = JogoGUI(tela, 'tutor_vs_b', 1.0, 'facil')
                        elif nome_botao == "vs Tutor (Médio)":
                            jogo = JogoGUI(tela, 'tutor_vs_b', 1.0, 'medio')
                        elif nome_botao == "vs Tutor (Difícil)":
                            jogo = JogoGUI(tela, 'tutor_vs_b', 1.0, 'dificil')
                        elif nome_botao == "Jogar de Pretas (Fácil)":
                            jogo = JogoGUI(tela, 'tutor_vs_p', 1.0, 'facil')
                        elif nome_botao == "Jogar de Pretas (Médio)":
                            jogo = JogoGUI(tela, 'tutor_vs_p', 1.0, 'medio')
                        elif nome_botao == "Jogar de Pretas (Difícil)":
                            jogo = JogoGUI(tela, 'tutor_vs_p', 1.0, 'dificil')
                        elif nome_botao == "Modo Análise (Tutor)":
                            jogo = JogoGUI(tela, 'tutor_analise')
                        elif nome_botao == "Treinar Doppelgänger":
                            treinar_modelo('doppelganger')
                            atualizar_estado_botoes()
                        elif nome_botao == "Treinar Mestre IA":
                            treinar_modelo('mestre')
                            atualizar_estado_botoes()

                        if jogo is not None:
                            estado_app = 'JOGANDO'


            elif estado_app == 'JOGANDO' and jogo:
                jogo.manager_painel.process_events(evento)

                if evento.type == pygame_gui.UI_BUTTON_PRESSED:
                    if evento.ui_element == jogo.botao_voltar_lance:
                        jogo.desfazer_lance()
                    elif evento.ui_element == jogo.botao_renderse:
                        jogo.render_se()

                if jogo.estado_jogo['fim_de_jogo']:
                    rect_revisar = pygame.Rect(LARGURA_TABULEIRO / 2 - 125 + LARGURA_BARRA_AVALIACAO,
                                               LARGURA_TABULEIRO / 2 + 60, 250, 50)
                    if evento.type == pygame.MOUSEBUTTONDOWN and rect_revisar.collidepoint(evento.pos):
                        if CAMINHO_STOCKFISH and jogo.modo_jogo in ['tutor_analise', 'tutor_vs_b', 'tutor_vs_p']:
                            revisao = RevisaoGUI(tela, jogo.lances_da_partida, jogo.historico_estados)
                            jogo.tutor.fechar_motor() if jogo.tutor else None
                            jogo = None
                            estado_app = 'REVISANDO'
                elif evento.type == pygame.MOUSEBUTTONDOWN:
                    if jogo.promovendo:
                        for rect, peca_escolhida in jogo.opcoes_promocao_rects:
                            if rect.collidepoint(evento.pos):
                                jogo.finalizar_promocao(peca_escolhida)
                                break
                    elif not jogo.animando and not jogo.turno_da_ia():
                        pos_mouse = pygame.mouse.get_pos()
                        offset_x = LARGURA_BARRA_AVALIACAO
                        if pos_mouse[0] > offset_x and pos_mouse[0] < LARGURA_TABULEIRO + offset_x and pos_mouse[
                            1] < LARGURA_TABULEIRO:
                            tela_col, tela_lin = (pos_mouse[0] - offset_x) // TAMANHO_CASA, pos_mouse[1] // TAMANHO_CASA
                            lin_motor, col_motor = (7 - tela_lin, 7 - tela_col) if jogo.tabuleiro_invertido else (
                                tela_lin, tela_col)
                            jogo.selecionar(lin_motor, col_motor)
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        if jogo and jogo.tutor: jogo.tutor.fechar_motor()
                        jogo = None;
                        estado_app = 'MENU'
                    elif evento.key == pygame.K_BACKSPACE and not jogo.animando:
                        jogo.desfazer_lance()

            elif estado_app == 'REVISANDO' and revisao:
                if evento.type == pygame.MOUSEBUTTONDOWN:
                    for nome, rect in revisao.botoes_revisao.items():
                        if rect.collidepoint(evento.pos):
                            if nome == 'inicio':
                                revisao.ir_para_inicio()
                            elif nome == 'anterior':
                                revisao.navegar_lance(-1)
                            elif nome == 'proximo':
                                revisao.navegar_lance(1)
                            elif nome == 'fim':
                                revisao.ir_para_fim()
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        revisao.fechar();
                        revisao = None;
                        estado_app = 'MENU'
                    elif evento.key == pygame.K_RIGHT:
                        revisao.navegar_lance(1)
                    elif evento.key == pygame.K_LEFT:
                        revisao.navegar_lance(-1)

        if estado_app == 'MENU':
            manager.update(time_delta)
            tela.fill(COR_MENU_FUNDO)
            manager.draw_ui(tela)
        elif estado_app == 'JOGANDO' and jogo:
            if jogo.animando:
                jogo.progresso_anim += jogo.velocidade_anim
                if jogo.progresso_anim >= 1.0:
                    jogo.progresso_anim = 0.0
                    jogo.animando = False
            elif jogo.turno_da_ia() and not jogo.estado_jogo['fim_de_jogo']:
                jogo.fazer_jogada_ia()

            jogo.manager_painel.update(time_delta)
            jogo.atualizar_painel_ui()
            jogo.desenhar_estado()
            jogo.manager_painel.draw_ui(tela)

            if jogo.estado_jogo['fim_de_jogo']:
                if CAMINHO_STOCKFISH and jogo.modo_jogo in ['tutor_analise', 'tutor_vs_b', 'tutor_vs_p']:
                    fonte_revisao = FONTE_BOTAO
                    rect_revisar = pygame.Rect(LARGURA_TABULEIRO / 2 - 125 + LARGURA_BARRA_AVALIACAO,
                                               LARGURA_TABULEIRO / 2 + 60, 250, 50)
                    pygame.draw.rect(tela, COR_BOTAO_HOVER, rect_revisar, border_radius=10)
                    texto_surface = fonte_revisao.render("Revisar Partida", True, COR_TEXTO)
                    tela.blit(texto_surface, texto_surface.get_rect(center=rect_revisar.center))
        elif estado_app == 'REVISANDO' and revisao:
            revisao.desenhar_revisao()

        pygame.display.flip()

    if jogo and jogo.tutor: jogo.tutor.fechar_motor()
    if revisao and revisao.tutor: revisao.tutor.fechar_motor()
    pygame.quit()


if __name__ == '__main__':
    loop_principal()