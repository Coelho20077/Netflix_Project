"""Package para carregar, pesquisar e analisar o catálogo Netflix (dataset Kaggle, 2023).

Módulos:
    data         leitura dos CSV e criação dos índices
    search       motor de pesquisa com critérios combináveis
    analysis     análise do catálogo (conteúdo, géneros, países, ratings)
    people       rede de atores e realizadores
    recommender  sistema de recomendação baseado em conteúdo
    temporal     evolução temporal do catálogo
    logger       configuração do ficheiro de log
    exceptions   exceções próprias do package
    utils        estatísticas simples sem numpy
"""

from netflix.data import load_titles, load_credits, load_dataset, build_index
from netflix.search import search, find_title
from netflix.people import build_people
from netflix.recommender import Recommender
from netflix.logger import setup_logging
from netflix.exceptions import (NetflixError, DataLoadError,
                                TitleNotFoundError, InvalidCriteriaError)

__all__ = [
    "load_titles", "load_credits", "load_dataset", "build_index",
    "search", "find_title", "build_people", "Recommender", "setup_logging",
    "NetflixError", "DataLoadError", "TitleNotFoundError", "InvalidCriteriaError",
]
