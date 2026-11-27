"""Base de datos SQLite del restaurante.

Todos los modulos guardan aca sus datos: la carta, las mesas, los clientes, las
comandas con sus platos y las ventas de la caja. SQLite viene incluido con
Python, asi que no hace falta instalar ni configurar ningun servidor: la base
completa es el archivo datos/restaurante.db.
"""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

CARPETA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos")
RUTA_BD = os.path.join(CARPETA, "restaurante.db")
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS productos (
    codigo     TEXT PRIMARY KEY,
    nombre     TEXT NOT NULL,
    precio     INTEGER NOT NULL,
    disponible INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS mesas (
    numero    INTEGER PRIMARY KEY,
    capacidad INTEGER NOT NULL,
    estado    TEXT NOT NULL DEFAULT 'Libre'
);
CREATE TABLE IF NOT EXISTS clientes (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre  TEXT NOT NULL,
    mesa    INTEGER,
    llegada TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS comandas (
    numero INTEGER PRIMARY KEY,
    mesa   INTEGER NOT NULL,
    mozo   TEXT NOT NULL,
    hora   TEXT NOT NULL,
    estado TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS items (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    comanda  INTEGER NOT NULL REFERENCES comandas(numero) ON DELETE CASCADE,
    codigo   TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    obs      TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS mozos (
    nombre TEXT PRIMARY KEY,
    alta   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ventas (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha    TEXT NOT NULL,
    mesa     INTEGER NOT NULL,
    comandas TEXT NOT NULL,
    subtotal INTEGER NOT NULL,
    iva      INTEGER NOT NULL,
    total    INTEGER NOT NULL
);
"""


@contextmanager
def conexion():
    """Abre la base, confirma los cambios si todo salio bien y la cierra siempre.

    Si algo falla en medio de una operacion, sqlite deshace todo lo que se habia
    escrito en ella, asi la base nunca queda a medio guardar.
    """
    nueva = not os.path.exists(RUTA_BD)
    os.makedirs(CARPETA, exist_ok=True)
    con = sqlite3.connect(RUTA_BD)
    con.row_factory = sqlite3.Row   # permite leer las columnas por nombre: fila["precio"]
    try:
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript(ESQUEMA)
        if nueva:
            _importar_json(con)
        with con:
            yield con
    finally:
        con.close()


def _importar_json(con):
    """La primera vez, trae a la base lo que ya estaba guardado en los JSON viejos."""
    menu_json = os.path.join(CARPETA, "menu.json")
    comandas_json = os.path.join(CARPETA, "comandas.json")
    try:
        if os.path.exists(menu_json):
            with open(menu_json, encoding="utf-8") as archivo:
                for codigo, p in json.load(archivo).items():
                    con.execute("INSERT OR IGNORE INTO productos VALUES (?, ?, ?, ?)",
                                (codigo, p["nombre"], p["precio"], int(p["disponible"])))
        if os.path.exists(comandas_json):
            with open(comandas_json, encoding="utf-8") as archivo:
                for c in json.load(archivo):
                    con.execute("INSERT OR IGNORE INTO comandas VALUES (?, ?, ?, ?, ?)",
                                (c["numero"], c["mesa"], c["mozo"], c["hora"], c["estado"]))
                    con.executemany(
                        "INSERT INTO items (comanda, codigo, cantidad, obs) VALUES (?, ?, ?, ?)",
                        [(c["numero"], i["codigo"], i["cantidad"], i.get("obs", "")) for i in c["items"]])
        con.commit()
    except (OSError, json.JSONDecodeError, KeyError):
        # Si un JSON viejo esta dañado no se importa, pero la base igual se crea
        con.rollback()


# Mesas: la clase Mesa sigue igual, solo se guarda y se recupera desde la base

def cargar_mesas():
    from modulos.mesa import Mesa   # se importa aca para no crear una dependencia circular
    mesas = {}
    with conexion() as con:
        for fila in con.execute("SELECT numero, capacidad, estado FROM mesas ORDER BY numero"):
            mesa = Mesa(fila["numero"], fila["capacidad"])
            mesa.estado = fila["estado"]
            mesas[mesa.numero] = mesa
    return mesas


def guardar_mesas(mesas):
    with conexion() as con:
        con.executemany(
            """INSERT INTO mesas (numero, capacidad, estado) VALUES (?, ?, ?)
               ON CONFLICT(numero) DO UPDATE SET capacidad = excluded.capacidad,
                                                 estado = excluded.estado""",
            [(m.numero, m.capacidad, m.estado) for m in mesas.values()])


# Clientes y ventas: se agregan como registros nuevos, nunca se reescriben

def registrar_cliente(nombre, mesa=None):
    with conexion() as con:
        con.execute("INSERT INTO clientes (nombre, mesa, llegada) VALUES (?, ?, ?)",
                    (nombre, mesa, datetime.now().strftime(FORMATO_FECHA)))


def clientes_de_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    with conexion() as con:
        return [dict(f) for f in con.execute(
            "SELECT nombre, mesa, llegada FROM clientes WHERE llegada LIKE ? ORDER BY id DESC",
            (hoy + "%",))]


def registrar_mozo(nombre):
    """Agrega un mozo al plantel; si ya estaba registrado no lo duplica."""
    with conexion() as con:
        con.execute("INSERT OR IGNORE INTO mozos (nombre, alta) VALUES (?, ?)",
                    (nombre, datetime.now().strftime(FORMATO_FECHA)))


def listar_mozos():
    with conexion() as con:
        return [f["nombre"] for f in con.execute("SELECT nombre FROM mozos ORDER BY nombre")]


def registrar_venta(mesa, numeros_comandas, subtotal, iva, total):
    with conexion() as con:
        con.execute(
            "INSERT INTO ventas (fecha, mesa, comandas, subtotal, iva, total) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().strftime(FORMATO_FECHA), mesa,
             ",".join(str(n) for n in numeros_comandas),
             round(subtotal), round(iva), round(total)))


def ventas_desde(fecha):
    with conexion() as con:
        return [dict(f) for f in con.execute(
            "SELECT fecha, mesa, comandas, subtotal, iva, total FROM ventas"
            " WHERE fecha >= ? ORDER BY id DESC", (fecha.strftime(FORMATO_FECHA),))]


def platos_vendidos_desde(fecha):
    """Suma las unidades de cada plato en las comandas entregadas o cobradas."""
    with conexion() as con:
        return [dict(f) for f in con.execute(
            """SELECT p.nombre AS plato, SUM(i.cantidad) AS cantidad
               FROM items i
               JOIN comandas c ON c.numero = i.comanda
               JOIN productos p ON p.codigo = i.codigo
               WHERE c.estado IN ('entregada', 'cobrada') AND c.hora >= ?
               GROUP BY p.nombre
               ORDER BY cantidad DESC""",
            (fecha.strftime(FORMATO_FECHA),))]
