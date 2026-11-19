"""Motor de pesquisa sobre o catálogo.

Ideia: cada critério dado pelo utilizador é transformado numa pequena função
(``filtro``) que recebe um título e devolve True/False. Um título entra no
resultado se passar em TODOS os filtros. Assim qualquer combinação de
critérios funciona com uma única função ``search`` — não é preciso escrever
uma função por combinação.

Exemplo do enunciado ("filmes de ação depois de 2015 com IMDb > 7.5")::

    search(titulos, content_type="MOVIE", genre="action",
           year_min=2016, imdb_min=7.5)
"""

import logging
import unicodedata

from netflix.exceptions import InvalidCriteriaError, TitleNotFoundError

logger = logging.getLogger(__name__)

SORT_FIELDS = {"title", "release_year", "runtime", "imdb_score", "imdb_votes",
               "tmdb_popularity", "tmdb_score"}


def normalize(texto):
    """Minúsculas e sem acentos, para pesquisas como 'pokemon' encontrarem 'Pokémon'."""
    texto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def _as_set(valor, maiusculas=False):
    """Aceita um valor único ou uma lista/tuplo/conjunto e devolve um conjunto."""
    if isinstance(valor, str):
        valor = [valor]
    if maiusculas:
        return {str(v).upper() for v in valor}
    return {str(v).lower() for v in valor}


def _check_range(nome, minimo, maximo):
    if minimo is not None and maximo is not None and minimo > maximo:
        raise InvalidCriteriaError(f"{nome}: mínimo ({minimo}) maior que máximo ({maximo})")


def _between(campo, minimo, maximo):
    """Cria um filtro 'minimo <= titulo[campo] <= maximo'.

    Títulos sem valor (None) nesse campo são excluídos, porque não sabemos se
    cumprem o critério.
    """
    def filtro(titulo):
        valor = titulo[campo]
        if valor is None:
            return False
        if minimo is not None and valor < minimo:
            return False
        if maximo is not None and valor > maximo:
            return False
        return True
    return filtro


def build_filters(title=None, content_type=None, year_min=None, year_max=None,
                  genre=None, genre_mode="all", age_rating=None, country=None,
                  imdb_min=None, imdb_max=None, min_votes=None,
                  runtime_min=None, runtime_max=None):
    """Transforma os critérios numa lista de funções-filtro.

    Está separada de ``search`` para poder ser testada sozinha e reutilizada
    (por exemplo, pelo recomendador).
    """
    _check_range("ano", year_min, year_max)
    _check_range("imdb", imdb_min, imdb_max)
    _check_range("duração", runtime_min, runtime_max)
    if genre_mode not in ("all", "any"):
        raise InvalidCriteriaError("genre_mode tem de ser 'all' ou 'any'")

    filtros = []

    if title is not None:
        procura = normalize(title)
        filtros.append(lambda t: procura in normalize(t["title"]))

    if content_type is not None:
        tipos = _as_set(content_type, maiusculas=True)
        invalidos = tipos - {"MOVIE", "SHOW"}
        if invalidos:
            raise InvalidCriteriaError(f"tipo inválido: {invalidos} (use MOVIE ou SHOW)")
        filtros.append(lambda t: t["type"] in tipos)

    if year_min is not None or year_max is not None:
        filtros.append(_between("release_year", year_min, year_max))

    if genre is not None:
        generos = _as_set(genre)
        if genre_mode == "all":
            # o título tem de ter todos os géneros pedidos
            filtros.append(lambda t: generos <= set(t["genres"]))
        else:
            # basta ter um dos géneros pedidos
            filtros.append(lambda t: bool(generos & set(t["genres"])))

    if age_rating is not None:
        classificacoes = _as_set(age_rating, maiusculas=True)
        filtros.append(lambda t: t["age_certification"] in classificacoes)

    if country is not None:
        paises = _as_set(country, maiusculas=True)
        filtros.append(lambda t: bool(paises & set(t["production_countries"])))

    if imdb_min is not None or imdb_max is not None:
        filtros.append(_between("imdb_score", imdb_min, imdb_max))

    if min_votes is not None:
        filtros.append(_between("imdb_votes", min_votes, None))

    if runtime_min is not None or runtime_max is not None:
        filtros.append(_between("runtime", runtime_min, runtime_max))

    return filtros


def search(titulos, sort_by=None, descending=True, limit=None, **criterios):
    """Pesquisa títulos da Netflix combinando vários critérios.

    Todos os critérios são opcionais e combinam-se com "E" lógico.

    Args:
        titulos: lista de títulos (de ``load_titles``).
        sort_by: campo pelo qual ordenar (ex.: "imdb_score"). None = ordem original.
        descending: ordem decrescente (True) ou crescente (False).
        limit: número máximo de resultados.
        **criterios: qualquer combinação de
            title (texto contido no título, sem distinguir maiúsculas/acentos),
            content_type ("MOVIE"/"SHOW"), year_min, year_max,
            genre (um género ou lista), genre_mode ("all" ou "any"),
            age_rating (uma classificação ou lista), country (código ou lista),
            imdb_min, imdb_max, min_votes, runtime_min, runtime_max.

    Returns:
        Lista dos títulos que cumprem todos os critérios.

    Raises:
        InvalidCriteriaError: critério desconhecido ou intervalo inválido.
    """
    try:
        filtros = build_filters(**criterios)
    except TypeError as erro:
        # Acontece quando se passa um critério que não existe (ex.: gnre=...)
        raise InvalidCriteriaError(f"critério desconhecido: {erro}") from erro

    resultados = [t for t in titulos if all(f(t) for f in filtros)]

    if sort_by is not None:
        if sort_by not in SORT_FIELDS:
            raise InvalidCriteriaError(f"não é possível ordenar por {sort_by!r}")
        # Os None vão sempre para o fim, independentemente da ordem
        com_valor = [t for t in resultados if t[sort_by] is not None]
        sem_valor = [t for t in resultados if t[sort_by] is None]
        com_valor.sort(key=lambda t: t[sort_by], reverse=descending)
        resultados = com_valor + sem_valor

    logger.info("Pesquisa %s -> %d resultados", criterios, len(resultados))

    if limit is not None:
        resultados = resultados[:limit]
    return resultados


def find_title(titulos, nome, content_type=None):
    """Encontra um título pelo nome exato (sem distinguir maiúsculas/acentos).

    Se houver vários com o mesmo nome (há ~50 casos no dataset), devolve o
    que tem mais votos no IMDb, que é normalmente o mais conhecido.

    Raises:
        TitleNotFoundError: se não existir nenhum título com esse nome.
    """
    alvo = normalize(nome.strip())
    candidatos = [t for t in titulos if normalize(t["title"]) == alvo]
    if content_type is not None:
        candidatos = [t for t in candidatos if t["type"] == content_type.upper()]
    if not candidatos:
        raise TitleNotFoundError(f"Título não encontrado: {nome!r}")
    return max(candidatos, key=lambda t: t["imdb_votes"] or 0)
