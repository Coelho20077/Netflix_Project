def search(titulos, title=None, type=None, year_min=None, year_max=None,
           genre=None, age_rating=None, country=None,
           imdb_min=None, imdb_max=None):
    """Pesquisa títulos da Netflix usando vários critérios."""

    resultados = []

    for titulo in titulos:

        if title is not None:
            if title.lower() not in titulo["title"].lower():
                continue

        if type is not None:
            if titulo["type"] != type:
                continue

        if year_min is not None:
            if titulo["release_year"] < year_min:
                continue

        if year_max is not None:
            if titulo["release_year"] > year_max:
                continue

        if genre is not None:
            if genre not in titulo["genres"]:
                continue

        if age_rating is not None:
            if titulo["age_certification"] != age_rating:
                continue

        if country is not None:
            if country not in titulo["production_countries"]:
                continue

        if imdb_min is not None:
            if titulo["imdb_score"] is None:
                continue

            if titulo["imdb_score"] < imdb_min:
                continue

        if imdb_max is not None:
            if titulo["imdb_score"] is None:
                continue

            if titulo["imdb_score"] > imdb_max:
                continue

        resultados.append(titulo)

    return resultados


