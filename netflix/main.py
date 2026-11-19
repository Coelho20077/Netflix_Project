from netflix.data import load_titles, load_credits
from netflix.search import search

titulos = load_titles()
creditos = load_credits()

resultados = search(
    titulos,
    country="US"
)

for titulo in resultados[:10]:
    print(titulo["title"], "-", titulo["production_countries"])



