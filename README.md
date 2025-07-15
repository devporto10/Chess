# ♟️ Xadrez com IA em Python

## 📜 Visão Geral

Este projeto é uma implementação completa de um jogo de xadrez em Python, utilizando **Pygame** para a interface gráfica. O seu principal diferencial é a arquitetura modular que suporta múltiplos tipos de Inteligência Artificial, incluindo um motor clássico, IAs baseadas em Machine Learning e uma integração com o poderoso motor **Stockfish** para análise e jogo.

---

## ✨ Funcionalidades

### Interface Gráfica Completa
- Tabuleiro interativo com destaque de movimentos.
- Histórico de lances.
- Captura de peças.

### Múltiplos Modos de Jogo
- Humano vs. Humano  
- Humano vs. IA (Minimax com Poda Alpha-Beta)  
- Humano vs. Mestre IA (Machine Learning treinado com jogos de mestres)  
- Humano vs. Doppelgänger IA (IA que imita o estilo de um jogador específico)  

### Tutor Inteligente (com Stockfish)
- **Oponente de Alto Nível**: Jogue contra o Stockfish com dificuldade ajustável.  
- **Análise em Tempo Real**: Avaliação da posição e sugestão do melhor lance.  
- **Comentários com IA Generativa**: O tutor "Dante", com a API do Google Gemini, explica a estratégia em linguagem natural.

### Ferramentas de Treinamento
- **Processador de PGN**: Script para extrair dados de treinamento de arquivos de partidas.
- **Treinamento Integrado**: Treine os modelos de Machine Learning diretamente pela interface do jogo.
- **Revisão de Partida**: Analise seus jogos lance a lance com o feedback do Stockfish.

---

## 📂 Estrutura do Projeto

.
├── gui.py # Interface gráfica e loop principal
├── regras_jogo.py # Regras do xadrez (xeque, fim de jogo, etc.)
├── logica_movimento.py # Validação de movimentos das peças
├── ia.py # IA clássica (Minimax com poda Alpha-Beta)
├── doppelganger.py # IAs com Machine Learning
├── tutor_stockfish.py # Integração com Stockfish e Google Gemini
├── processar_pgn.py # Processamento de arquivos PGN
├── utils.py # Funções utilitárias
├── assets/ # Imagens, sons, fontes, executável do Stockfish

yaml
Copiar
Editar

---

## 🚀 Como Executar

### 1. Pré-requisitos

- Python 3.9+
- Executável do Stockfish (https://stockfishchess.org/download/)
- (Opcional) Chave de API do Google Gemini

### 2. Instalação

bash
git clone https://github.com/seuusuario/xadrez-ia.git
cd xadrez-ia
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install pygame pygame-gui python-chess pandas scikit-learn google-generativeai
Coloque o executável do Stockfish dentro da pasta assets/.

(Opcional) Crie um arquivo config.ini na raiz do projeto:

ini
Copiar
Editar
[API]
GOOGLE_API_KEY = SUA_CHAVE_AQUI
3. Execução
bash
Copiar
Editar
python gui.py
4. Treinando a IA (Opcional)
Coloque o arquivo .pgn na raiz do projeto (ex: partidas_mestres.pgn)

Gere os dados de treino:

bash
Copiar
Editar
python processar_pgn.py
No menu principal do jogo, clique em "Treinar Mestre IA".

🛠️ Arquitetura
O sistema usa um dicionário de estado do jogo para armazenar todas as informações da partida.

A lógica de movimentação é separada da interface gráfica.

Os motores de IA são selecionáveis diretamente no menu do jogo.

A IA baseada em Machine Learning utiliza RandomForestClassifier, que prevê o melhor movimento com base em um hash único da posição do tabuleiro.

🔮 Melhorias Futuras
✅ Salvar e carregar jogos

📖 Adicionar um livro de aberturas para as IAs

🧠 Melhorar a função de avaliação da IA Minimax (controle de centro, segurança do rei)

🌐 Implementar modo de jogo online

