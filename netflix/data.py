"""Leitura e preparação dos dados (titles.csv e credits.csv).

Estrutura de dados escolhida
----------------------------
* ``titulos``: lista de dicionários, um por título. É a estrutura natural para
  percorrer o catálogo inteiro (pesquisa, contagens, análise temporal).
  Os campos ``genres`` e ``production_countries`` passam de texto
  ("['drama', 'crime']") para listas Python.
* ``creditos``: lista de dicionários, um por participação (pessoa, título, papel).
* ``indice``: dicionário ``{id_do_titulo: dicionario_do_titulo}``. Serve para
  ligar os créditos aos títulos em O(1), em vez de procurar na lista toda
  (O(n)) para cada uma das ~80 mil linhas de créditos.
"""

import ast
import csv
import logging
import os

from netflix.exceptions import DataLoadError

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

TITLES_COLUMNS = {
    "id", "title", "type", "description", "release_year", "age_certification",
    "runtime", "genres", "production_countries", "seasons", "imdb_id",
    "imdb_score", "imdb_votes", "tmdb_popularity", "tmdb_score",
}
CREDITS_COLUMNS = {"person_id", "id", "name", "character", "role"}


# ---------------------------------------------------------------------------
# Leitura genérica
# ---------------------------------------------------------------------------

def load_csv(nome_ficheiro, colunas_obrigatorias=None):
    """Carrega um ficheiro CSV e devolve uma lista de dicionários.

    Args:
        nome_ficheiro: caminho para o ficheiro.
        colunas_obrigatorias: conjunto de colunas que o ficheiro tem de ter.

    Raises:
        DataLoadError: se o ficheiro não existir, não puder ser lido ou não
            tiver as colunas obrigatórias.
    """
    try:
        with open(nome_ficheiro, "r", encoding="utf8", newline="") as file:
            leitor = csv.DictReader(file)
            colunas = set(leitor.fieldnames or [])
            if colunas_obrigatorias:
                em_falta = colunas_obrigatorias - colunas
                if em_falta:
                    raise DataLoadError(
                        f"{nome_ficheiro}: faltam as colunas {sorted(em_falta)}"
                    )
            dados = list(leitor)
    except FileNotFoundError as erro:
        logger.error("Ficheiro não encontrado: %s", nome_ficheiro)
        raise DataLoadError(f"Ficheiro não encontrado: {nome_ficheiro}") from erro
    except (UnicodeDecodeError, csv.Error) as erro:
        logger.error("Erro a ler %s: %s", nome_ficheiro, erro)
        raise DataLoadError(f"Não foi possível ler {nome_ficheiro}: {erro}") from erro
    except DataLoadError as erro:
        logger.error(str(erro))
        raise

    logger.info("Lidas %d linhas de %s", len(dados), os.path.basename(nome_ficheiro))
    return dados


# ---------------------------------------------------------------------------
# Conversões de campos (cada uma devolve None se o valor estiver vazio/inválido)
# ---------------------------------------------------------------------------

def _to_int(valor):
    if valor is None or valor.strip() == "":
        return None
    return int(float(valor))      # "1.0" (seasons) -> 1


def _to_float(valor):
    if valor is None or valor.strip() == "":
        return None
    return float(valor)


def _to_text(valor):
    if valor is None or valor.strip() == "":
        return None
    return valor.strip()


def _to_list(valor):
    """Converte "['drama', 'crime']" numa lista. Texto inválido -> lista vazia.

    Usamos ast.literal_eval (e não eval) porque só aceita literais Python,
    não executa código.
    """
    if valor is None or valor.strip() == "":
        return []
    resultado = ast.literal_eval(valor)
    if not isinstance(resultado, list):
        raise ValueError(f"esperava uma lista, obtive {valor!r}")
    return [str(x).strip() for x in resultado if str(x).strip()]


# ---------------------------------------------------------------------------
# titles.csv
# ---------------------------------------------------------------------------

def _prepare_title(linha):
    """Converte os campos de uma linha de titles.csv para os tipos certos."""
    titulo = {
        "id": linha["id"].strip(),
        "title": linha["title"].strip(),
        "type": linha["type"].strip().upper(),          # MOVIE ou SHOW
        "description": _to_text(linha["description"]),
        "release_year": _to_int(linha["release_year"]),
        "age_certification": _to_text(linha["age_certification"]),
        "runtime": _to_int(linha["runtime"]),
        "genres": _to_list(linha["genres"]),
        "production_countries": _to_list(linha["production_countries"]),
        "seasons": _to_int(linha["seasons"]),
        "imdb_id": _to_text(linha["imdb_id"]),
        "imdb_score": _to_float(linha["imdb_score"]),
        "imdb_votes": _to_int(linha["imdb_votes"]),
        "tmdb_popularity": _to_float(linha["tmdb_popularity"]),
        "tmdb_score": _to_float(linha["tmdb_score"]),
    }

    # Validações mínimas: sem id, título ou ano a linha não serve para nada
    if not titulo["id"] or not titulo["title"] or titulo["release_year"] is None:
        raise ValueError("id, title ou release_year em falta")
    if titulo["type"] not in ("MOVIE", "SHOW"):
        raise ValueError(f"tipo desconhecido: {titulo['type']}")

    # Duração 0 não é real (são 19 casos no dataset): tratamos como em falta
    if titulo["runtime"] == 0:
        titulo["runtime"] = None

    # Ratings fora da escala 0-10 são considerados erro de dados
    if titulo["imdb_score"] is not None and not 0 <= titulo["imdb_score"] <= 10:
        titulo["imdb_score"] = None

    return titulo


def load_titles(caminho=None):
    """Carrega e prepara os dados dos títulos da Netflix.

    Linhas mal formatadas são ignoradas e registadas no log (o programa não
    pára por causa de uma linha má).

    Args:
        caminho: caminho para titles.csv (por omissão data/titles.csv).

    Returns:
        Lista de dicionários, um por título.
    """
    if caminho is None:
        caminho = os.path.join(DATA_DIR, "titles.csv")

    linhas = load_csv(caminho, TITLES_COLUMNS)
    titulos = []
    ids_vistos = set()
    rejeitadas = 0

    # numero_linha começa em 2 porque a linha 1 é o cabeçalho
    for numero_linha, linha in enumerate(linhas, start=2):
        try:
            titulo = _prepare_title(linha)
        except (ValueError, SyntaxError, KeyError) as erro:
            rejeitadas += 1
            logger.warning("titles.csv linha %d ignorada: %s", numero_linha, erro)
            continue

        if titulo["id"] in ids_vistos:
            rejeitadas += 1
            logger.warning("titles.csv linha %d ignorada: id repetido %s",
                           numero_linha, titulo["id"])
            continue

        ids_vistos.add(titulo["id"])
        titulos.append(titulo)

    logger.info("Títulos carregados: %d (rejeitados: %d)", len(titulos), rejeitadas)
    return titulos


# ---------------------------------------------------------------------------
# credits.csv
# ---------------------------------------------------------------------------

def load_credits(caminho=None, indice=None):
    """Carrega os créditos (atores e realizadores).

    Args:
        caminho: caminho para credits.csv (por omissão data/credits.csv).
        indice: dicionário {id: título}. Se for dado, os créditos de títulos
            que não existem no catálogo são descartados.

    Returns:
        Lista de dicionários com person_id, id, name, character, role.
    """
    if caminho is None:
        caminho = os.path.join(DATA_DIR, "credits.csv")

    linhas = load_csv(caminho, CREDITS_COLUMNS)
    creditos = []
    vistos = set()
    duplicados = 0
    rejeitadas = 0

    for numero_linha, linha in enumerate(linhas, start=2):
        role = (linha["role"] or "").strip().upper()
        credito = {
            "person_id": (linha["person_id"] or "").strip(),
            "id": (linha["id"] or "").strip(),
            "name": (linha["name"] or "").strip(),
            "character": _to_text(linha["character"]),
            "role": role,
        }

        if not credito["person_id"] or not credito["id"] or not credito["name"] \
                or role not in ("ACTOR", "DIRECTOR"):
            rejeitadas += 1
            logger.warning("credits.csv linha %d ignorada: dados incompletos",
                           numero_linha)
            continue

        if indice is not None and credito["id"] not in indice:
            rejeitadas += 1
            continue

        # A mesma pessoa pode aparecer duas vezes no mesmo título com o
        # mesmo papel (ex.: dobra duas personagens). Para contar
        # participações só interessa uma vez.
        chave = (credito["person_id"], credito["id"], role)
        if chave in vistos:
            duplicados += 1
            continue
        vistos.add(chave)
        creditos.append(credito)

    logger.info("Créditos carregados: %d (duplicados removidos: %d, rejeitados: %d)",
                len(creditos), duplicados, rejeitadas)
    return creditos


# ---------------------------------------------------------------------------
# Índices e carregamento completo
# ---------------------------------------------------------------------------

def build_index(titulos):
    """Cria o dicionário {id_do_titulo: título} para acesso direto por id."""
    return {titulo["id"]: titulo for titulo in titulos}


def credits_by_title(creditos):
    """Agrupa os créditos por título: {id_do_titulo: [créditos]}."""
    grupos = {}
    for credito in creditos:
        grupos.setdefault(credito["id"], []).append(credito)
    return grupos


def load_dataset(data_dir=None):
    """Carrega os dois ficheiros e devolve tudo o que o resto do package precisa.

    Returns:
        Tuplo (titulos, creditos, indice).
    """
    if data_dir is None:
        data_dir = DATA_DIR
    titulos = load_titles(os.path.join(data_dir, "titles.csv"))
    indice = build_index(titulos)
    creditos = load_credits(os.path.join(data_dir, "credits.csv"), indice)
    return titulos, creditos, indice
