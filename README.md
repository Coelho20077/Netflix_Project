# Netflix Catalog Analyzer

Package Python para carregar, pesquisar e analisar o catálogo de filmes e séries da Netflix (EUA, março de 2023), a partir do dataset [Netflix Movies and TV Shows](https://www.kaggle.com/datasets/victorsoeiro/netflix-tv-shows-and-movies) do Kaggle.

Implementado só com a biblioteca standard do Python (sem pandas, numpy ou bibliotecas de machine learning).

## Funcionalidades

| Módulo | O que faz |
|---|---|
| `netflix/data.py` | Lê `titles.csv` e `credits.csv`, converte os tipos, valida as linhas e cria o índice por id |
| `netflix/search.py` | Pesquisa com qualquer combinação de critérios (título, tipo, anos, género, classificação etária, rating, votos, país, duração), com ordenação e limite |
| `netflix/analysis.py` | Contagens por tipo, géneros e países mais frequentes, distribuição e estatísticas dos ratings, rating por género, top de títulos |
| `netflix/people.py` | Rede de atores e realizadores: rankings, rating médio por realizador, atores multi-género, pessoas que foram ator e realizador, colaborações frequentes |
| `netflix/recommender.py` | `Recommender.recommend(title, n)`: recomendação por semelhança de géneros, descrição (TF-IDF), pessoas, países, tipo e ano |
| `netflix/temporal.py` | Evolução por ano/período: nº de títulos, filmes e séries, géneros, ratings, duração e origem geográfica |
| `netflix/logger.py` | Configuração do ficheiro de log `logs/netflix.log` |
| `netflix/exceptions.py` | Exceções próprias (`DataLoadError`, `TitleNotFoundError`, `InvalidCriteriaError`) |
| `netflix/utils.py` | Média, mediana, desvio padrão e outras funções auxiliares |

## Estrutura do projeto

```
Netflix_Project/
├── data/
│   ├── titles.csv
│   └── credits.csv
├── netflix/            # o package
│   ├── __init__.py
│   ├── data.py
│   ├── search.py
│   ├── analysis.py
│   ├── people.py
│   ├── recommender.py
│   ├── temporal.py
│   ├── logger.py
│   ├── exceptions.py
│   └── utils.py
├── logs/netflix.log    # criado ao correr o programa
├── main.py             # demonstração de todas as funcionalidades
└── README.md
```

## Instalação

1. Python 3.10 ou superior. Não há dependências externas para o package (o Jupyter só é necessário para abrir o notebook).
2. Clonar o repositório:
   ```bash
   git clone <url-do-repositorio>
   cd Netflix_Project
   ```
3. Descarregar `titles.csv` e `credits.csv` do Kaggle e colocá-los na pasta `data/`.

## Utilização

Correr a demonstração completa:

```bash
python main.py
```

Usar o package no próprio código ou num notebook (a partir da pasta do projeto):

```python
from netflix import setup_logging, load_dataset, search, build_people, Recommender
from netflix import analysis, people, temporal

setup_logging()
titulos, creditos, indice = load_dataset()

# Filmes de ação lançados depois de 2015 com IMDb > 7.5
search(titulos, content_type="MOVIE", genre="action", year_min=2016,
       imdb_min=7.5, sort_by="imdb_score", limit=10)

# Análise
analysis.genre_counts(titulos, n=10)
analysis.rating_distribution(titulos)

# Atores e realizadores
rede = build_people(creditos)
people.top_actors(rede, 10)
people.director_ratings(rede, indice, min_titles=3)

# Recomendação
rec = Recommender(titulos, creditos)
rec.recommend("Stranger Things", 5)
rec.explain("Stranger Things", "Dark")   # porque são semelhantes

# Evolução temporal
temporal.genre_trends(titulos, split_year=2015)
temporal.rating_evolution(titulos, period=5)
```

### Critérios de pesquisa

Todos são opcionais e combinam-se com "E":

| Critério | Exemplo |
|---|---|
| `title` | `title="pokemon"` (contém, ignora maiúsculas e acentos) |
| `content_type` | `"MOVIE"` ou `"SHOW"` |
| `year_min`, `year_max` | `year_min=2010, year_max=2015` |
| `genre`, `genre_mode` | `genre=["comedy", "family"]` (todos) ou `genre_mode="any"` (algum) |
| `age_rating` | `"PG-13"` ou `["G", "PG"]` |
| `country` | `"PT"` ou `["ES", "MX"]` |
| `imdb_min`, `imdb_max`, `min_votes` | `imdb_min=7, min_votes=5000` |
| `runtime_min`, `runtime_max` | `runtime_max=90` (minutos) |
| `sort_by`, `descending`, `limit` | `sort_by="imdb_score", limit=10` |

## Sistema de recomendação

A semelhança entre dois títulos é uma soma pesada de seis componentes, todas entre 0 e 1:

| Componente | Medida | Peso |
|---|---|---|
| Géneros | Jaccard | 0.35 |
| Descrição | Cosseno entre vetores TF-IDF | 0.30 |
| Atores/realizadores | Jaccard | 0.15 |
| Países | Jaccard | 0.10 |
| Tipo (filme/série) | 1 se igual | 0.05 |
| Ano | 1 − \|Δano\| / 30 | 0.05 |

Os resultados são ordenados por score decrescente e, em caso de empate, pelo rating IMDb. Os pesos podem ser alterados: `Recommender(titulos, creditos, weights={"description": 0.5})`.

## Logs e erros

Cada execução acrescenta ao ficheiro `logs/netflix.log` o início e o fim da execução, o número de títulos e créditos carregados, as linhas rejeitadas, as pesquisas feitas e os erros encontrados.

Ficheiros em falta ou ilegíveis dão origem a `DataLoadError`. Linhas mal formatadas são ignoradas e ficam registadas no log, sem parar o programa.

## Limitações do dataset

- Tem só o ano de lançamento, não a data em que o título entrou na Netflix.
- Representa o catálogo dos EUA em março de 2023, não o catálogo atual.
- Há valores em falta: cerca de 470 títulos não têm rating IMDb e cerca de 2700 não têm classificação etária.
- Nas séries, `runtime` é a duração de um episódio.

## Autores

| Nº | Nome | GitHub |
|---|---|---|
|  |  |  |
|  |  |  |
|  |  |  |
