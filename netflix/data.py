import csv
import ast
import os


def load_csv(nome_ficheiro):
    """Carrega um ficheiro CSV e devolve uma lista de dicionários."""
    with open(nome_ficheiro, "r", encoding="utf8") as file:
        leitor = csv.DictReader(file)
        dados = list(leitor)

    return dados


def load_titles():
    """Carrega e prepara os dados dos títulos da Netflix."""
    caminho = os.path.join("data", "titles.csv")
    titulos = load_csv(caminho)

    for titulo in titulos:
        titulo["release_year"] = int(titulo["release_year"])
        titulo["runtime"] = int(titulo["runtime"])

        if titulo["imdb_score"] != "":
            try:
                titulo["imdb_score"] = float(titulo["imdb_score"])
            except ValueError:
                titulo["imdb_score"] = None
        else:
            titulo["imdb_score"] = None

        if titulo["imdb_votes"] != "":
            try:
                titulo["imdb_votes"] = float(titulo["imdb_votes"])
            except ValueError:
                titulo["imdb_votes"] = None
        else:
            titulo["imdb_votes"] = None

        if titulo["age_certification"] == "":
            titulo["age_certification"] = None

        titulo["genres"] = ast.literal_eval(titulo["genres"])
        titulo["production_countries"] = ast.literal_eval(
            titulo["production_countries"]
        )

    return titulos


def load_credits():

    caminho = os.path.join("data", "credits.csv")
    return load_csv(caminho)

