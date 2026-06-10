# SAD_P1 -- Analise What-If: Simulacao de Lucro em Loja de Varejo

Ferramenta de apoio a decisao que permite simular diferentes cenarios de
precificacao em uma loja de varejo e estimar o lucro resultante em cada caso.
Faz parte da disciplina Sistemas de Apoio a Decisao (SAD).

## Descricao do problema

Uma loja deseja entender como alteracoes nos precos dos produtos impactam o
lucro final. O modelo permite variar os precos (para cima ou para baixo) e
observar o efeito sobre o lucro total, a margem de cada produto e o ranking
dos cenarios mais vantajosos.

## Funcionalidades

- Carregamento de dados via arquivo CSV com precos, custos e quantidades.
- Modo interativo com menu textual para simulacao passo a passo.
- Modo linha de comando para execucao rapida de cenarios.
- Cenarios automaticos pre-definidos (Otimista, Pessimista, Foco em Volume,
  Premium), com opcao de executa-los individualmente ou em lote.
- Visualizacao grafica com tres paineis:
  - Lucro por produto: base versus melhor cenario.
  - Variacao de lucro por produto no melhor cenario.
  - Comparativo de lucro total entre todos os cenarios simulados.
- Recomendacao do cenario mais vantajoso com destaque para o produto de maior
  ganho, o de maior perda e alerta de margem baixa.
- Exportacao automatica do grafico em PNG (grafico_whatif.png).

## Dados de entrada

O arquivo `produtos.csv` deve conter as seguintes colunas:

| Coluna             | Descricao                             |
| ------------------ | ------------------------------------- |
| produto            | Nome do produto                       |
| categoria          | Categoria (Vestuario, Calcados, etc.) |
| preco_atual        | Preco de venda atual (R$)             |
| custo_unitario     | Custo unitario do produto (R$)        |
| quantidade_vendida | Unidades vendidas no periodo          |

O projeto ja inclui um arquivo de exemplo com 15 produtos em 3 categorias.

## Como usar

### Modo interativo (recomendado)

```bash
python analise_whatif.py
```

O programa exibe um menu com as seguintes opcoes:

- **1** -- Aplica uma variacao percentual unica a todos os produtos.
- **2** -- Aplica variacoes individuais, produto por produto.
- **3** -- Abre o submenu de cenarios automaticos pre-definidos.
- **R** -- Exibe a recomendacao e os graficos com base nos cenarios ja
  simulados (so aparece apos o primeiro cenario ser registrado).
- **0** -- Encerra o programa, mostrando a recomendacao final e os graficos.

### Modo linha de comando

```bash
python analise_whatif.py --global 10      # aplica +10% em todos os produtos
python analise_whatif.py --global -15     # aplica -15% em todos os produtos
python analise_whatif.py --auto           # executa os 4 cenarios automaticos
python analise_whatif.py --lista          # lista os produtos disponiveis
```

### Cenarios automaticos

Ao escolher a opcao `3` no menu interativo (ou `--auto` na linha de comando),
quatro cenarios pre-configurados ficam disponiveis:

| #   | Cenario     | Regra                                                       |
| --- | ----------- | ----------------------------------------------------------- |
| 1   | Otimista    | +10% nos produtos com margem acima da media; +5% nos demais |
| 2   | Pessimista  | -15% em todos os produtos (simula crise/retracao)           |
| 3   | Foco Volume | -10% nos 5 produtos mais vendidos; +8% nos demais           |
| 4   | Premium     | +20% apenas nos 5 produtos de menor volume                  |

E possivel escolher um cenario especifico (`1` a `4`), executar todos de uma
vez (`A`) ou voltar ao menu (`0`).

## Dependencias

O projeto requer **Python 3.9 ou superior** e as bibliotecas listadas abaixo.

### Instalacao das bibliotecas

```bash
pip install pandas matplotlib numpy
```

| Biblioteca | Finalidade                                    |
| ---------- | --------------------------------------------- |
| pandas     | Leitura do CSV e manipulacao dos dados        |
| matplotlib | Geracao dos graficos de barras e comparativos |
| numpy      | Operacoes numericas auxiliares                |

As tres bibliotecas sao amplamente utilizadas em analise de dados e estao
disponiveis no indice oficial do PyPI. Nao ha dependencias externas alem
destas.

## Estrutura do projeto

```
SAD_P1/
  analise_whatif.py   -- Codigo principal
  produtos.csv        -- Base de dados dos produtos
  README.md           -- Este arquivo
  grafico_whatif.png  -- Graficos explicativos
```
