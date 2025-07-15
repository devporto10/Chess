class RevisaoGUI:
    def __init__(self, t, l, h):
        self.tela = t;
        self.lances_da_partida = l;
        self.historico_estados = h;
        self.indice_lance_atual = -1;
        self.tutor = Tutor();
        self.feedback_atual = "Use as setas para revisar.";
        self.estado_jogo_exibido = self.historico_estados[0]
        y = LARGURA_TABULEIRO + 45
        w, s = 50, 15
        x = LARGURA_TABULEIRO + LARGURA_BARRA_AVALIACAO + (PAINEL_LATERAL - (4 * w + 3 * s)) / 2
        self.botoes_revisao = {'inicio': pygame.Rect(x, y, w, 35),
                               'anterior': pygame.Rect(x + w + s, y, w, 35),
                               'proximo': pygame.Rect(x + 2 * (w + s), y, w, 35),
                               'fim': pygame.Rect(x + 3 * (w + s), y, w, 35)}
        self.analisar_lance_atual()

    def navegar_lance(self, d):
        n = self.indice_lance_atual + d;
        self.indice_lance_atual = n if -1 <= n < len(self.lances_da_partida) else self.indice_lance_atual;
        self.analisar_lance_atual()

    def ir_para_inicio(self):
        self.indice_lance_atual = -1;
        self.analisar_lance_atual()

    def ir_para_fim(self):
        self.indice_lance_atual = len(self.lances_da_partida) - 1 if self.lances_da_partida else -1;
        self.analisar_lance_atual()

    def analisar_lance_atual(self):
        if self.indice_lance_atual == -1:
            self.estado_jogo_exibido = self.historico_estados[0]
            self.feedback_atual = "Posição inicial."
            return

        e_a = self.historico_estados[self.indice_lance_atual]
        e_d = self.historico_estados[self.indice_lance_atual + 1]
        l_f = self.lances_da_partida[self.indice_lance_atual]
        self.estado_jogo_exibido = e_d;
        l_u = uci_para_movimento(l_f);
        self.feedback_atual = "Analisando...";
        self.desenhar_revisao();
        pygame.display.flip();
        analise = self.tutor.gerar_comentario_geral(e_d, e_a, l_u)

        if isinstance(analise, dict):
            self.feedback_atual = analise.get('feedback_texto', '...')
            score = analise.get('score', 0.0)
            melhor_lance = analise.get('melhor_lance', 'N/A')
            self.feedback_atual += f"\n\nScore: {score:.2f}\nMelhor: {melhor_lance}"
        else:
            self.feedback_atual = str(analise)

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
                    self.tela.blit(IMAGENS_PECAS[p], (c * TAMANHO_CASA, r * TAMANHO_CASA))

    def fechar(self):
        if self.tutor: self.tutor.fechar_motor()