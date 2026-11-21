"""Ayudas de pantalla compartidas por todos los modulos.

Aqui viven los colores, la limpieza de pantalla y las funciones que PIDEN datos
validandolos: si el usuario se equivoca, se muestra un aviso en rojo con un
ejemplo de lo que hay que escribir y se vuelve a preguntar.

Uso en cualquier modulo:
    from modulos.entrada import pedir_texto, pedir_entero, ok, error

Este archivo solo usa la libreria estandar: funciona aunque no esten
instaladas rich ni pyfiglet.
"""

import os
import sys

# ---------------------------------------------------------------------
# Colores y pantalla
# ---------------------------------------------------------------------
if sys.stdout.isatty():
    if os.name == "nt":
        os.system("")  # activa los colores en la terminal de Windows
    COLORES = {"verde": "\033[92m", "rojo": "\033[91m", "amarillo": "\033[93m",
               "celeste": "\033[96m", "gris": "\033[90m", "blanco": "\033[97m"}
    FIN_COLOR = "\033[0m"
else:
    # Sin terminal real (por ejemplo, salida a un archivo) no se usan colores
    COLORES = dict.fromkeys(
        ["verde", "rojo", "amarillo", "celeste", "gris", "blanco"], "")
    FIN_COLOR = ""


def pintar(texto, color):
    return COLORES[color] + texto + FIN_COLOR


def limpiar():
    """Borra la pantalla para que no se acumulen pantallas viejas."""
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")
    else:
        print()


def titulo(texto):
    linea = "=" * (len(texto) + 8)
    print(pintar(linea, "celeste"))
    print(pintar("    " + texto, "celeste"))
    print(pintar(linea, "celeste"))


def _con_etiqueta(etiqueta, texto, color):
    """Imprime el texto con una etiqueta al inicio y todo en un mismo color.

    Si el texto tiene varias lineas (separadas con \n), solo la primera lleva
    la etiqueta; las demas se sangran para que queden alineadas debajo."""
    lineas = texto.split("\n")
    sangria = " " * (len(etiqueta) + 1)
    print(pintar(etiqueta + " " + lineas[0], color))
    for linea in lineas[1:]:
        print(pintar(sangria + linea.strip(), color))


def ok(texto):
    """Resultado exitoso: se muestra en verde."""
    _con_etiqueta("[OK]", texto, "verde")


def error(texto):
    """Error del usuario: se muestra en ROJO y explica el motivo y como corregirlo."""
    _con_etiqueta("[ERROR]", texto, "rojo")


def aviso(texto):
    """Advertencia o informacion importante: se muestra en amarillo."""
    _con_etiqueta("[!]", texto, "amarillo")


def info(texto):
    print(pintar(texto, "gris"))


def mostrar_mensaje(mensaje):
    """Muestra un mensaje (tipo, texto) guardado de la accion anterior."""
    if not mensaje:
        return
    tipo, texto = mensaje
    {"ok": ok, "error": error, "aviso": aviso}.get(tipo, info)(texto)


def pausa():
    """Espera un Enter para que el resultado se pueda leer antes de limpiar."""
    print(pintar("\nPresione Enter para continuar...", "gris"), end="", flush=True)
    input()


# ---------------------------------------------------------------------
# Pedir datos con validacion
# ---------------------------------------------------------------------
def pedir(etiqueta, ejemplo=""):
    """Pregunta un dato mostrando entre parentesis que hay que escribir.

    El input() va sin colores para que la escritura funcione bien en
    cualquier terminal."""
    if ejemplo:
        etiqueta = etiqueta + " " + pintar("(" + ejemplo + ")", "gris")
    print(etiqueta + ": ", end="", flush=True)
    return input().strip()


def pedir_texto(etiqueta, ejemplo, minimo=2, maximo=40, solo_letras=False,
                cancelable=True):
    """Pide un texto. Devuelve el texto, o None si el usuario cancela con Enter.

    solo_letras=True acepta letras, espacios, guion y apostrofe (nombres de personas).
    """
    # La pista le muestra al usuario un ejemplo de respuesta correcta
    pista = "ej.: " + ejemplo + (", Enter vacio cancela" if cancelable else "")
    while True:   # se repite la pregunta hasta que el dato sea valido o se cancele
        texto = " ".join(pedir(etiqueta, pista).split())   # quita espacios de mas
        # Cada rama siguiente es una validacion distinta, con su propio mensaje en rojo
        if not texto:
            if cancelable:
                aviso("Cancelado: no se guardo nada.")
                return None
            error("Este dato es obligatorio. Escriba por ejemplo: " + ejemplo)
        elif len(texto) < minimo:
            error(f"Muy corto: escriba al menos {minimo} letras. Por ejemplo: {ejemplo}")
        elif len(texto) > maximo:
            error(f"Muy largo: maximo {maximo} caracteres (escribio {len(texto)}).")
        elif solo_letras and not all(c.isalpha() or c in " -'." for c in texto):
            error("Use solo letras y espacios, sin numeros ni simbolos. "
                  f"Por ejemplo: {ejemplo}")
        else:
            return texto   # paso todas las validaciones


def pedir_entero(etiqueta, ejemplo, minimo=1, maximo=None, cancelable=True):
    """Pide un numero entero dentro de un rango. Devuelve el numero, o None si cancela."""
    # Texto del rango permitido, se reutiliza en la pista y en los mensajes de error
    rango = f"de {minimo} a {maximo}" if maximo is not None else f"minimo {minimo}"
    pista = f"numero {rango}, ej.: {ejemplo}" + (", Enter vacio cancela" if cancelable else "")
    while True:
        texto = pedir(etiqueta, pista)
        if not texto:
            if cancelable:
                aviso("Cancelado: no se guardo nada.")
                return None
            error(f"Este dato es obligatorio. Escriba un numero {rango}, por ejemplo {ejemplo}.")
            continue
        # Debe ser un entero: se rechazan letras, decimales y simbolos
        if not texto.lstrip("-").isdigit():
            error(f"'{texto}' no es un numero entero. Escriba solo digitos, por ejemplo {ejemplo}.")
            continue
        valor = int(texto)
        # Rango: evita valores absurdos como la mesa 2222 o capacidad 0
        if valor < minimo or (maximo is not None and valor > maximo):
            error(f"{valor} esta fuera del rango permitido: escriba un numero {rango}.")
            continue
        return valor


def pedir_si_no(pregunta):
    """Pregunta de si o no. Devuelve True para si, False para no."""
    while True:
        r = pedir(pregunta, "s = si, n = no").lower()   # acepta mayusculas y minusculas
        if r in ("s", "si", "sí"):
            return True
        if r in ("n", "no"):
            return False
        error("Responda con  s  (si)  o  n  (no).")


def pedir_opcion(etiqueta, validas, ejemplo=None):
    """Pide una opcion de menu. Devuelve el texto escrito, siempre uno de 'validas'."""
    validas = [str(v) for v in validas]   # se comparan siempre como texto
    ejemplo = ejemplo or validas[0]
    while True:
        r = pedir(etiqueta, f"escriba el numero y Enter, ej.: {ejemplo}")
        if r in validas:
            return r
        error(f"'{r}' no es una opcion. Elija una de: {', '.join(validas)}.")
