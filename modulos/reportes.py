"""Reportes de ventas a partir de las comandas guardadas por el Mozo.

Lee datos/comandas.json con pandas y dibuja con matplotlib que platos salieron
mas en el dia o en la semana. Se abre desde el modulo Menu.
"""
import json
import os
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")   # dibuja directo a un archivo, sin abrir una ventana que bloquee la consola
import matplotlib.pyplot as plt
import pandas as pd

from modulos.entrada import error, ok, pedir
from modulos.mozo import ARCHIVO, ENTREGADA, FORMATO_HORA

# Solo cuentan como venta las comandas que ya llegaron a la mesa o se cobraron
VENDIDAS = (ENTREGADA, "cobrada")
# Los graficos van dentro de datos/, que ya esta en el .gitignore y no se sube a GitHub
CARPETA_REPORTES = os.path.join(os.path.dirname(ARCHIVO), "reportes")


def cargar_ventas(carta):
    """Arma una tabla con una fila por plato vendido: fecha, plato, cantidad e importe."""
    if not os.path.exists(ARCHIVO):
        return pd.DataFrame()
    try:
        with open(ARCHIVO, encoding="utf-8") as archivo:
            comandas = json.load(archivo)
    except (OSError, json.JSONDecodeError):
        return pd.DataFrame()

    filas = []
    for comanda in comandas:
        if comanda.get("estado") not in VENDIDAS:
            continue
        for item in comanda["items"]:
            producto = carta.obtener(item["codigo"])
            precio = producto.precio if producto else 0
            filas.append({
                "fecha": datetime.strptime(comanda["hora"], FORMATO_HORA),
                "plato": producto.nombre if producto else item["codigo"],
                "cantidad": item["cantidad"],
                "importe": precio * item["cantidad"],
            })
    return pd.DataFrame(filas)


def _guardar(fig, nombre_archivo):
    os.makedirs(CARPETA_REPORTES, exist_ok=True)
    ruta = os.path.join(CARPETA_REPORTES, nombre_archivo)
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    return ruta


def mas_vendidos(ventas, desde, titulo, nombre_archivo):
    """Grafica en barras horizontales los platos mas pedidos a partir de una fecha."""
    periodo = ventas[ventas["fecha"] >= desde]
    if periodo.empty:
        return None

    # groupby junta las filas del mismo plato y suma las cantidades, como en la Unidad 40
    ranking = periodo.groupby("plato")["cantidad"].sum().sort_values()

    fig, ax = plt.subplots(figsize=(8, 4.5))
    barras = ax.barh(ranking.index, ranking.values, color="#C8553D")
    barras[-1].set_color("#2E4A3A")   # el mas vendido queda destacado en otro color
    ax.bar_label(barras, padding=4)
    ax.set_title(titulo, loc="left", fontsize=13, fontweight="bold")
    ax.set_xlabel("Unidades vendidas")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _guardar(fig, nombre_archivo)


def mostrar_reportes(carta):
    """Pregunta que reporte se quiere ver, dibuja el grafico y lo abre."""
    ventas = cargar_ventas(carta)
    if ventas.empty:
        error("Todavía no hay comandas entregadas o cobradas para analizar.")
        return

    print("  1. Lo más pedido hoy")
    print("  2. Lo más pedido en la semana")
    tipo = pedir("Reporte", "1 o 2")

    ahora = datetime.now()
    # La semana son los ultimos 7 dias completos contando hoy, desde la medianoche
    inicio_semana = (ahora - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    inicio_hoy = ahora.replace(hour=0, minute=0, second=0, microsecond=0)

    if tipo == "1":
        ruta = mas_vendidos(ventas, inicio_hoy, "Lo más pedido hoy",
                            "mas_vendidos_hoy.png")
    elif tipo == "2":
        ruta = mas_vendidos(ventas, inicio_semana, "Lo más pedido en los últimos 7 días",
                            "mas_vendidos_semana.png")
    else:
        error(f"'{tipo}' no es un reporte. Escriba 1 o 2.")
        return

    if ruta is None:
        error("No hay ventas en ese período.")
        return
    ok(f"Gráfico guardado en {ruta}")
    # En Windows el grafico se abre solo con el visor de imagenes
    if hasattr(os, "startfile"):
        os.startfile(ruta)
