# tutor_stockfish.py (Corrigido)

import chess
import chess.engine
import os
import subprocess
import configparser
import random
from utils import converter_notacao_para_indices, uci_para_movimento, resource_path

try:
    import google.generativeai as genai
except ImportError:
    genai = None


def encontrar_executavel_stockfish():
    nomes_possiveis = ['stockfish.exe', 'stockfish', 'stockfish-windows-x86-64-avx2.exe', 'stockfish-windows-x86-64',
                       'stockfish-ubuntu-x86-64-avx2', 'stockfish-ubuntu-x86-64', '123', '123.exe']
    for nome in nomes_possiveis:
        caminho_relativo = os.path.join('assets', nome)
        caminho_absoluto = resource_path(caminho_relativo)
        if os.path.exists(caminho_absoluto): return caminho_absoluto
    return None


def ler_chave_api():
    config = configparser.ConfigParser()
    caminho_config = resource_path('config.ini')
    if os.path.exists(caminho_config):
        config.read(caminho_config)
        return config.get('API', 'GOOGLE_API_KEY', fallback=None)
    return None


CAMINHO_STOCKFISH = encontrar_executavel_stockfish()
GOOGLE_API_KEY = ler_chave_api()
USE_LLM = bool(GOOGLE_API_KEY and GOOGLE_API_KEY != "AIzaSyDgj2gStv6ClCFfibrmirYTfH29GkyEffI" and genai)

if USE_LLM:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        print("INFO: API do Google Gemini configurada com sucesso.")
    except Exception as e:
        print(f"ERRO: Falha ao configurar API do Gemini: {e}")
        USE_LLM = False


def get_startup_info():
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return startupinfo
    return None


class Tutor:
    def __init__(self):
        self.motor = None
        if CAMINHO_STOCKFISH:
            try:
                self.motor = chess.engine.SimpleEngine.popen_uci([CAMINHO_STOCKFISH], startupinfo=get_startup_info())
            except Exception as e:
                print(f"ERRO ao iniciar Stockfish para o Tutor: {e}")

    def _chamar_llm(self, prompt, tipo_comentario):
        try:
            print(f"INFO: Contatando API do Gemini para: {tipo_comentario}...")
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            response = model.generate_content(prompt)
            feedback_texto = response.text.strip()
            print(f"DEBUG [Tutor/LLM]: Resposta recebida da API -> '{feedback_texto}'")
            return feedback_texto
        except Exception as e:
            print(f"ERRO na API do Gemini ({tipo_comentario}): {e}")
            if "quota" in str(e).lower():
                return "Atingimos nossa cota de conversa por hoje! Continuaremos amanhã."
            return "Hmm, tive um problema para pensar. Vamos continuar."

    def _analisar_posicao(self, fen, tempo_analise=0.5):
        if not self.motor: return None, None
        try:
            tabuleiro = chess.Board(fen)
            self.motor.configure({"Skill Level": 20})
            info = self.motor.analyse(tabuleiro, chess.engine.Limit(time=tempo_analise))
            return info.get("score").white(), info.get("pv")[0] if info.get("pv") else None
        except Exception as e:
            print(f"ERRO ao analisar posição com Stockfish: {e}")
            return None, None

    def gerar_comentario_geral(self, estado_jogo, estado_antes=None, lance_jogador_uci=None):
        if not self.motor:
            return {"feedback_texto": "Tutor indisponível.", "score": 0.0, "melhor_lance": "N/A"}

        fen_atual = converter_estado_para_fen(estado_jogo)
        score_obj_atual, melhor_lance_obj_atual = self._analisar_posicao(fen_atual)

        if score_obj_atual is None:
            return {"feedback_texto": "Erro ao analisar posição.", "score": 0.0, "melhor_lance": "N/A"}

        pontuacao_cp_atual = score_obj_atual.score(mate_score=30000)
        score_final_perspectiva_brancas = pontuacao_cp_atual / 100.0
        melhor_lance_uci_atual = melhor_lance_obj_atual.uci() if melhor_lance_obj_atual else "N/A"

        feedback_texto = ""

        if estado_antes and lance_jogador_uci:
            feedback_texto = self._gerar_texto_analise_lance(estado_antes, estado_jogo, score_obj_atual,
                                                             lance_jogador_uci, melhor_lance_uci_atual)
        else:
            if USE_LLM:
                if random.random() < 0.2 and len(estado_jogo['notacao_lances']) > 6:
                    feedback_texto = self._gerar_comentario_filler()
                elif len(estado_jogo['notacao_lances']) < 6:
                    feedback_texto = self._gerar_comentario_abertura(estado_jogo)
                else:
                    feedback_texto = self._gerar_comentario_estrategico(estado_jogo)
            else:
                feedback_texto = "Sua vez de jogar."

        return {
            "feedback_texto": feedback_texto,
            "score": score_final_perspectiva_brancas,
            "melhor_lance": melhor_lance_uci_atual
        }

    def _gerar_texto_analise_lance(self, estado_antes, estado_depois, score_depois_obj, lance_jogador_uci,
                                   melhor_lance_uci_sugerido):
        fen_antes = converter_estado_para_fen(estado_antes)
        score_antes_obj, _ = self._analisar_posicao(fen_antes)

        if score_antes_obj is None or score_depois_obj is None:
            return "Tutor: Erro ao avaliar a posição."

        pontuacao_antes_cp = score_antes_obj.score(mate_score=30000)
        pontuacao_depois_cp = score_depois_obj.score(mate_score=30000)

        delta = (pontuacao_depois_cp - pontuacao_antes_cp) * (-1 if estado_antes['turno'] == 'preto' else 1)
        classificacao = self._classificar_lance(delta)

        feedback_texto = ""
        if USE_LLM and (classificacao in ["Brilhante!", "Erro."]):
            fen_depois = converter_estado_para_fen(estado_depois)
            feedback_texto = self._gerar_feedback_llm_analise(classificacao, melhor_lance_uci_sugerido, fen_depois,
                                                              lance_jogador_uci)
        else:
            feedback_texto = f"{classificacao}"
            if melhor_lance_uci_sugerido != "N/A" and melhor_lance_uci_sugerido != lance_jogador_uci and classificacao != "Brilhante!":
                feedback_texto += f" Um bom lance aqui seria {melhor_lance_uci_sugerido}."

        return feedback_texto

    def _gerar_comentario_filler(self):
        prompt = "Aja como um tutor de xadrez amigável chamado Dante. Faça uma pergunta curta e pessoal sobre xadrez ou sobre a vida para o jogador, em português do Brasil. Ex: 'O que te fez começar a jogar xadrez?' ou 'Qual seu jogador favorito?' ou 'Este tipo de posição me lembra um jogo que tive semana passada.'."
        return self._chamar_llm(prompt, "Comentário Filler")

    def _gerar_comentario_abertura(self, estado_jogo):
        lances = estado_jogo['notacao_lances']
        pares_de_lances = []
        for i in range(0, len(lances), 2):
            num_lance = (i // 2) + 1
            lance_branco = lances[i]
            if i + 1 < len(lances):
                lance_preto = lances[i + 1]
                pares_de_lances.append(f"{num_lance}. {lance_branco} {lance_preto}")
            else:
                pares_de_lances.append(f"{num_lance}. {lance_branco}")

        lances_notacao = " ".join(pares_de_lances)
        prompt = f"Aja como um tutor de xadrez amigável chamado Dante. A partida começou com os seguintes lances: {lances_notacao}. Identifique o nome da abertura (se houver um) e dê um comentário curto (1-2 frases) sobre sua ideia principal. Fale em português do Brasil."
        return self._chamar_llm(prompt, "Comentário de Abertura")

    def _gerar_comentario_estrategico(self, estado_jogo):
        fen = converter_estado_para_fen(estado_jogo);
        ultimo_lance_ia_uci = uci_para_movimento(estado_jogo['ultimo_movimento']) if estado_jogo[
            'ultimo_movimento'] else "Nenhum (início do jogo)"
        prompt = f"Aja como um tutor de xadrez amigável, em português do Brasil. É a vez do jogador humano ({estado_jogo['turno']}). Meu último lance foi: {ultimo_lance_ia_uci}. A posição FEN é: {fen}. Explique em uma frase a ideia por trás do meu lance ({ultimo_lance_ia_uci}). Depois, em outra frase, dê uma dica estratégica geral para o humano, sem revelar o melhor lance."
        return self._chamar_llm(prompt, "Comentário Estratégico")

    def _classificar_lance(self, delta_cp):
        if delta_cp >= 100: return "Brilhante!";
        if delta_cp >= 30: return "Ótimo lance!";
        if delta_cp > -30: return "Bom lance.";
        if delta_cp > -100: return "Imprecisão.";
        return "Erro."

    def _gerar_feedback_llm_analise(self, classificacao, melhor_lance, fen, lance_jogador):
        prompt_intro = f"Aja como um tutor de xadrez amigável, positivo e didático em português do Brasil. A posição atual do tabuleiro no formato FEN é: {fen}. O jogador humano acabou de fazer o lance: {lance_jogador}."
        if classificacao == "Brilhante!":
            prompt_task = f'Minha análise da situação é que o lance do humano foi classificado como "{classificacao}". Forneça um feedback curto e encorajador (1 a 2 frases) elogiando o jogador. Explique em termos conceituais simples (1 a 2 frases) por que o lance {lance_jogador} foi tão forte.'
        else:
            prompt_task = f'Minha análise da situação é a seguinte: Classificação do lance do humano: "{classificacao}". A melhor jogada sugerida pelo motor Stockfish nesta posição era: {melhor_lance}. Forneça um feedback curto e encorajador de 2 a 3 frases. Se houver uma sugestão melhor ({melhor_lance}), explique em termos conceituais simples (1 a 2 frases) por que ela é forte.'
        prompt = prompt_intro + prompt_task
        return self._chamar_llm(prompt, "Análise de Lance com LLM")

    def fechar_motor(self):
        if self.motor: self.motor.quit()


def encontrar_melhor_movimento_tutor(estado_jogo, tempo_limite, dificuldade='dificil'):
    if not CAMINHO_STOCKFISH: return None
    fen = converter_estado_para_fen(estado_jogo);
    board = chess.Board(fen)
    if board.is_game_over(): return None

    MAPA_DIFICULDADE = {
        'facil': 5,
        'medio': 13,
        'dificil': 20
    }
    skill_level = MAPA_DIFICULDADE.get(dificuldade, 20)

    try:
        with chess.engine.SimpleEngine.popen_uci([CAMINHO_STOCKFISH], startupinfo=get_startup_info()) as engine:
            engine.configure({"Skill Level": skill_level})
            print(f"INFO: Tutor/Oponente jogando com Skill Level: {skill_level}")

            resultado = engine.play(board, chess.engine.Limit(time=tempo_limite))
            inicio, fim = converter_notacao_para_indices(resultado.move.uci()[:2]), converter_notacao_para_indices(
                resultado.move.uci()[2:4])
            return (inicio, fim)
    except Exception as e:
        print(f"ERRO ao buscar movimento do Tutor: {e}")
        return None


def converter_estado_para_fen(estado_jogo):
    fen_tabuleiro = '';
    for r in range(8):
        vazios = 0
        for c in range(8):
            peca = estado_jogo['tabuleiro'][r][c]
            if peca == '.':
                vazios += 1
            else:
                if vazios > 0: fen_tabuleiro += str(vazios); vazios = 0
                fen_tabuleiro += peca
        if vazios > 0: fen_tabuleiro += str(vazios)
        if r < 7: fen_tabuleiro += '/'
    turno_fen = 'w' if estado_jogo['turno'] == 'branco' else 'b'
    hist = estado_jogo['historico_movimento']
    roque_fen = ""
    rei_branco_moveu = hist.get('K', False)
    torre_h1_moveu = hist.get('R_h1', False)
    torre_a1_moveu = hist.get('R_a1', False)
    rei_preto_moveu = hist.get('k', False)
    torre_h8_moveu = hist.get('r_h8', False)
    torre_a8_moveu = hist.get('r_a8', False)

    if not rei_branco_moveu and not torre_h1_moveu: roque_fen += 'K'
    if not rei_branco_moveu and not torre_a1_moveu: roque_fen += 'Q'
    if not rei_preto_moveu and not torre_h8_moveu: roque_fen += 'k'
    if not rei_preto_moveu and not torre_a8_moveu: roque_fen += 'q'

    if not roque_fen: roque_fen = '-'

    alvo_ep = estado_jogo.get('alvo_en_passant');
    alvo_ep_fen = '-'
    if alvo_ep:
        r, c = alvo_ep;
        # A notação FEN para en passant é a casa *atrás* do peão que acabou de mover.
        if estado_jogo['turno'] == 'branco':  # Se é a vez das brancas, o peão preto avançou 2 casas.
            alvo_ep_fen = f"{chr(ord('a') + c)}{8 - (r - 1)}"
        else:  # Se é a vez das pretas, o peão branco avançou 2 casas.
            alvo_ep_fen = f"{chr(ord('a') + c)}{8 - (r + 1)}"

    meio_lance_fen = str(estado_jogo.get('contador_50_lances', 0))
    num_meio_lances = len(estado_jogo.get('notacao_lances', []))
    lance_completo_fen = str((num_meio_lances // 2) + 1)
    return f"{fen_tabuleiro} {turno_fen} {roque_fen} {alvo_ep_fen} {meio_lance_fen} {lance_completo_fen}"