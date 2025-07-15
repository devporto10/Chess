# doppelganger.py

import pickle
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from regras_jogo import gerar_hash_posicao, gerar_todos_movimentos_legais
from utils import resource_path

# Mapeamento de nome do modelo para nome do arquivo de dados/modelo
MODEL_CONFIG = {
    'doppelganger': {
        'data_file': 'dados_treino.csv',
        'model_file': 'modelo_doppelganger.pkl'
    },
    'mestre': {
        'data_file': 'dados_mestres.csv',
        'model_file': 'modelo_mestre.pkl'
    }
}


def carregar_modelo(nome_modelo):
    """Carrega um modelo treinado do disco."""
    caminho_modelo = resource_path(MODEL_CONFIG[nome_modelo]['model_file'])
    if not os.path.exists(caminho_modelo):
        print(f"ERRO: Arquivo do modelo '{caminho_modelo}' não encontrado.")
        return None
    with open(caminho_modelo, 'rb') as f:
        return pickle.load(f)


def prever_movimento(estado_jogo, nome_modelo):
    """
    Prevê o melhor movimento para a posição atual usando o modelo treinado.
    Retorna o movimento no formato ((r_ini, c_ini), (r_fim, c_fim)).
    """
    modelo = carregar_modelo(nome_modelo)
    if modelo is None:
        return None  # Retorna None se o modelo não puder ser carregado

    # 1. Obter todos os movimentos legais da posição atual
    movimentos_legais = gerar_todos_movimentos_legais(
        estado_jogo['tabuleiro'],
        estado_jogo['turno'],
        estado_jogo['historico_movimento'],
        estado_jogo['alvo_en_passant']
    )

    if not movimentos_legais:
        return None

    # 2. Gerar o hash da posição atual
    hash_atual = gerar_hash_posicao(
        estado_jogo['tabuleiro'],
        estado_jogo['turno'],
        estado_jogo['historico_movimento'],
        estado_jogo['alvo_en_passant']
    )

    # 3. Preparar os dados para o modelo (precisamos do formato DataFrame)
    # A entrada para o modelo é o hash da posição.
    # Como o modelo foi treinado com features one-hot, precisamos criar um DataFrame
    # com as mesmas colunas que o modelo espera.

    # Criamos um dicionário para a nossa única linha de dados
    dados_posicao = {col: [0] for col in modelo.feature_names_in_}

    # Marcamos o hash da nossa posição atual como 1
    if hash_atual in dados_posicao:
        dados_posicao[hash_atual][0] = 1

    df_posicao = pd.DataFrame(dados_posicao)

    # 4. Usar o modelo para prever as probabilidades de cada movimento possível
    # O modelo prevê a probabilidade para cada CLASSE (movimento) que ele conhece.
    probabilidades = modelo.predict_proba(df_posicao)[0]

    # Mapeia as probabilidades para os nomes das classes (movimentos em formato string)
    movimentos_prob = {modelo.classes_[i]: prob for i, prob in enumerate(probabilidades)}

    # 5. Encontrar o melhor movimento LEGAL
    melhor_movimento_legal = None
    maior_prob = -1

    for movimento in movimentos_legais:
        # Converte o movimento legal (tupla) para a string que o modelo entende
        movimento_str = str(movimento)

        # Pega a probabilidade prevista para este movimento
        prob = movimentos_prob.get(movimento_str, 0)

        if prob > maior_prob:
            maior_prob = prob
            melhor_movimento_legal = movimento

    if melhor_movimento_legal:
        print(
            f"INFO [{nome_modelo.upper()}]: Movimento escolhido {melhor_movimento_legal} com probabilidade {maior_prob:.2f}")
    else:
        # Se nenhum movimento legal foi encontrado nas previsões, retorna o primeiro legal
        print(f"AVISO [{nome_modelo.upper()}]: Nenhum movimento previsto era legal. Escolhendo um aleatoriamente.")
        return movimentos_legais[0] if movimentos_legais else None

    return melhor_movimento_legal


def treinar_modelo(nome_modelo):
    """
    Lê os dados de um arquivo CSV e treina um modelo de classificação.
    """
    config = MODEL_CONFIG[nome_modelo]
    caminho_csv = resource_path(config['data_file'])
    caminho_modelo_saida = resource_path(config['model_file'])

    if not os.path.exists(caminho_csv):
        print(f"ERRO: Arquivo de dados '{caminho_csv}' não encontrado. Execute o processador de PGN primeiro.")
        return

    print(f"--- Iniciando treinamento do modelo '{nome_modelo.upper()}' ---")
    print(f"Lendo dados de '{caminho_csv}'...")
    df = pd.read_csv(caminho_csv)

    # O hash da posição é nossa feature, o movimento é nosso alvo (target)
    # Usamos get_dummies para transformar os hashes em colunas (one-hot encoding)
    X = pd.get_dummies(df['posicao'])
    y = df['movimento']

    print("Dividindo dados para treino e teste...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Treinando o modelo RandomForestClassifier... (Isso pode levar um momento)")
    # Usamos um classificador simples e robusto
    modelo = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    modelo.fit(X_train, y_train)
    print("Treinamento concluído.")

    print("Avaliando o modelo...")
    y_pred = modelo.predict(X_test)
    precisao = accuracy_score(y_test, y_pred)
    print(f"Precisão do modelo no conjunto de teste: {precisao * 100:.2f}%")

    print(f"Salvando modelo treinado em '{caminho_modelo_saida}'...")
    with open(caminho_modelo_saida, 'wb') as f:
        pickle.dump(modelo, f)

    print("--- Processo de treinamento finalizado com sucesso! ---")