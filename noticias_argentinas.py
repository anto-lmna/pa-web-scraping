import requests
from bs4 import BeautifulSoup
import concurrent.futures
import time
import pandas as pd


# Definimos la url que se va a usar y los headers a la hora de mandar solicitudes
url_base = "https://www.argentina.gob.ar/noticias"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 115Browser/27.0.2.1"
}


# Esta función extrae de cada página los enlaces a cada noticia
def extraer_links(nro_paginas: int) -> list:
    links = []

    for n in range(0, nro_paginas + 1):
        try:
            r = requests.get(f"{url_base}?page={n}", headers=headers)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, "html.parser")
            divs_titulares = soup.find_all("div", class_="col-xs-12 col-sm-3")

            for div in divs_titulares:
                for link in div.find_all("a", href=True):
                    # Al enlace original le incluimos la url de cada una de las noticias
                    links.append(f"https://www.argentina.gob.ar{link['href']}")

            time.sleep(2)  # Evita sobrecargar el servidor

        except requests.RequestException as e:
            print(f"Error al obtener los enlaces: {e}")
            continue

    return links


# Con esta función extraemos el titulo, subtitulo y fecha de cada una de las noticias
def extraer_info(link: str) -> dict:
    try:
        r = requests.get(link, headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")

        # Extraer título
        div_titulo = soup.find("div", class_="title-description")
        titulo = div_titulo.h1.get_text() if div_titulo else "Título no disponible"

        # Extraer subtítulo
        div_subtitulo = soup.find("div", class_="news__lead")
        subtitulo = (
            div_subtitulo.p.get_text()
            if div_subtitulo and div_subtitulo.p
            else "Subtítulo no disponible"
        )

        # Extraer fecha
        fecha = soup.find("time", class_="text-muted")
        fecha = fecha.get_text().strip() if fecha else "Fecha no disponible"

        return {"titulo": titulo, "subtitulo": subtitulo, "fecha": fecha}
    # Manejar Error
    except requests.RequestException as e:
        print(f"Error al obtener la noticia: {e}")
        return None


# Esta función mide el tiempo de ejecución de una función
def medir_tiempo(func, *args):
    tiempo_inicio = time.time()
    resultado = func(*args)
    tiempo_final = time.time()
    return resultado, tiempo_final - tiempo_inicio


# Función para comparar el tiempo dependiendo los hilos que se usen
def medir_tiempo_hilos(num_hilos):
    links_noticias = extraer_links(1)
    tiempo_inicio = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_hilos) as executor:
        detalle_noticia = executor.map(extraer_info, links_noticias)
        listado_noticias = [noticia for noticia in detalle_noticia if noticia]

    tiempo_final = time.time()
    return tiempo_final - tiempo_inicio


# Ejecución concurrente con diferentes números de hilos
def ejecutar_concurrente_hilos():
    resultados_tiempos = {}
    for hilos in [1, 2, 4, 8]:
        tiempo = medir_tiempo_hilos(hilos)
        resultados_tiempos[hilos] = tiempo
        print(f"Tiempo con {hilos} hilo(s): {tiempo:.2f} segundos")


# Enlaces de las noticias
links_noticias = extraer_links(1)


# Ejecución no concurrente
def ejecutar_no_concurrente(links_noticias):
    todas_noticias = []
    for link in links_noticias:
        info_noticia = extraer_info(link)
        if info_noticia:
            todas_noticias.append(info_noticia)
    return todas_noticias


# Ejecución concurrente
def ejecutar_concurrente(links_noticias):
    with concurrent.futures.ThreadPoolExecutor() as ex:
        detalle_noticia = ex.map(extraer_info, links_noticias)
        return [noticia for noticia in detalle_noticia if noticia]


# Ejecución de la función no concurrente con medición de tiempo
listado_noticias, tiempo_no_concurrente = medir_tiempo(
    ejecutar_no_concurrente, links_noticias
)

# Ejecución de la función concurrente con medición de tiempo
listado_noticias_concurrente, tiempo_concurrente = medir_tiempo(
    ejecutar_concurrente, links_noticias
)

# Comparación resultados
print(
    f"El tiempo de ejecución no concurrente es de: {tiempo_no_concurrente:.2f} segundos para {len(listado_noticias)} noticias"
)
print(
    f"El tiempo de ejecución concurrente es de: {tiempo_concurrente:.2f} segundos para {len(listado_noticias_concurrente)} noticias"
)


# Guardamos la información que recolectamos a un archivo csv
df = pd.DataFrame(listado_noticias_concurrente)
df.to_csv("recopilacion_noticias.csv", index=False)
