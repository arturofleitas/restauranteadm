"""restauranteadm: sistema de restaurante con comandas y cobro digital.

main.py es el unico archivo que se ejecuta:  python main.py
Crea los datos compartidos, muestra el menu principal y abre cada modulo.
La portada visual la dibuja modulos/interfaz.py; aqui solo se decide que hacer."""

import os
import sys

from modulos import caja, cliente, mesa, mozo
from modulos import menu as carta_menu
from modulos import pass_ as pase
from modulos.menu import Carta
from modulos.mozo import EN_PREPARACION, LISTA, PENDIENTE, ENTREGADA Mozo

# La portada usa las librerias rich y pyfiglet (pip install -r requirements.txt).
# Si no estan instaladas, el programa funciona igual con el menu de texto simple.
try:
    from modulos.interfaz import mostrar_inicio
except ImportError:
    mostrar_inicio = None

# Unica lista de opciones del menu principal: la usan la portada y el menu simple.
OPCIONES = [
    ("1", "Cliente"),
    ("2", "Gestión de Mesas"),
    ("3", "Menú (Carta)"),
    ("4", "Mozo (Comandas)"),
    ("5", "Pass (Cocina)"),
    ("6", "Caja"),
    ("7", "Ayuda: cómo usar el sistema"),
    ("0", "Salir"),
]

# Orientacion que se muestra al entrar a cada modulo: para que sirve y que escribir.
AYUDA_MODULO = {
    "1": ["CLIENTE: registra a la persona que llega al restaurante.",
          "Nombre: escriba nombre y apellido, por ejemplo  Ana Gonzalez"],
    "2": ["MESAS: registre las mesas del local y marquelas ocupadas o libres.",
          "Numero de mesa: un entero mayor que cero, por ejemplo  1",
          "Capacidad: cantidad de personas, por ejemplo  4",
          "Una mesa debe estar OCUPADA para que el mozo pueda tomarle el pedido."],
    "3": ["MENU: consulte la carta, busque platos y vea precios.",
          "Codigos de platos: letra y numero, por ejemplo  P1  (plato) o  B2  (bebida)",
          "Presupuesto: guaranies sin puntos ni comas, por ejemplo  100000"],
    "4": ["MOZO: abra la comanda de una mesa, cargue los platos y enviela a cocina.",
          "Nombre del mozo: por ejemplo  Lucas",
          "Numero de mesa: una mesa ya registrada y ocupada, por ejemplo  1",
          "Codigo del plato: por ejemplo  P1 ; escriba  0  para terminar de cargar",
          "Observacion: texto libre, por ejemplo  sin cebolla  (o Enter si no hay)"],
    "6": ["CAJA: consulte los pedidos entregados y cobre la cuenta de la mesa.",
          "Numero de mesa: escriba el numero de la mesa a cobrar, por ejemplo  1"],
}


# ---------------------------------------------------------------------
# Ayudas de pantalla: colores, limpiar la terminal y pedir datos.
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


def ok(texto):
    print(pintar("[OK] " + texto, "verde"))


def error(texto):
    print(pintar("[ERROR] " + texto, "rojo"))


def aviso(texto):
    print(pintar("[!] " + texto, "amarillo"))


def info(texto):
    print(pintar(texto, "gris"))


def pedir(etiqueta, ejemplo=""):
    """Pregunta un dato mostrando entre parentesis que hay que escribir."""
    if ejemplo:
        etiqueta = etiqueta + " " + pintar("(" + ejemplo + ")", "gris")
    print(etiqueta + ": ", end="", flush=True)
    return input().strip()


def pausa():
    """Espera un Enter para que el resultado se pueda leer antes de limpiar."""
    print(pintar("\nPresione Enter para continuar...", "gris"), end="", flush=True)
    input()


class Restaurante:
    """Datos que comparten todos los modulos durante la ejecucion."""

    def __init__(self):
        self.carta = Carta()   # una sola carta para Menu, Mozo y Pass
        self.mesas = {}        # numero de mesa -> objeto Mesa


def mostrar_guia():
    """Explica el recorrido completo del sistema, de la llegada al cobro."""
    limpiar()
    titulo("COMO USAR EL SISTEMA")
    print("\nEl sistema sigue el recorrido de un cliente en el restaurante:\n")
    pasos = [
        ("2. Gestión de Mesas", "Registre las mesas del local (una sola vez)."),
        ("1. Cliente", "Llega un cliente: registre su nombre."),
        ("2. Gestión de Mesas", "Ocupe la mesa donde se sienta."),
        ("4. Mozo", "Abra la comanda, cargue los platos y enviela a cocina."),
        ("5. Pass", "La cocina prepara el pedido y lo marca como listo."),
        ("4. Mozo", "Entregue en la mesa la comanda lista."),
        ("6. Caja", "Cobre la cuenta y emita el ticker de pago"),
        ("2. Gestión de Mesas", "Libere la mesa para el proximo cliente."),
    ]
    for numero, (donde, que) in enumerate(pasos, start=1):
        print(f"  Paso {numero}:  {pintar(donde.ljust(20), 'celeste')} {que}")
    print()
    info("En cada campo se muestra un ejemplo de lo que hay que escribir.")
    info("En cualquier submenu, la opcion 0 vuelve al menu anterior.")
    info("El menu principal indica siempre cual es el siguiente paso.")
    info("Esta guia se puede volver a ver con la opcion 7.")
    pausa()


def siguiente_paso(restaurante):
    """Mira el estado del restaurante y sugiere que hacer ahora."""
    comandas = Mozo("Sistema")
    listas = len(comandas.por_estado(LISTA))
    en_cocina = len(comandas.por_estado(EN_PREPARACION))
    abiertas = len(comandas.por_estado(PENDIENTE))
    mesas = restaurante.mesas
    ocupadas = [m for m in mesas.values() if m.estado == "Ocupada"]
    entregadas = len(comandas.por_estado(ENTREGADA))

    if entregadas:
        return (f"Hay {entregadas} comanda(s) entregada(s). Entre a 6. Caja"
                " para cobrar la cuenta.")
    if listas:
        return (f"Hay {listas} comanda(s) lista(s). Entre a 4. Mozo y elija"
                " 'Entregar comanda lista'.")
    if en_cocina:
        return (f"Hay {en_cocina} comanda(s) en cocina. Entre a 5. Pass para"
                " marcarlas como listas.")
    if abiertas:
        return (f"Hay {abiertas} comanda(s) sin enviar. Entre a 4. Mozo y elija"
                " 'Enviar comanda a la cocina'.")
    if not mesas:
        return "Empiece por 2. Gestión de Mesas y registre las mesas del local."
    if not ocupadas:
        return ("Cuando llegue un cliente: registrelo en 1. Cliente y ocupe"
                " una mesa en 2. Gestión de Mesas.")
    return ("Hay mesas ocupadas. Tome el pedido en 4. Mozo ('Abrir comanda');"
            " si ya terminaron, libere la mesa en 2. Gestión de Mesas.")


def mostrar_menu(restaurante):
    """Dibuja el menu principal: con la portada si se puede, o en texto simple."""
    if mostrar_inicio is not None:
        mostrar_inicio(restaurante.mesas, OPCIONES)
    else:
        limpiar()
        titulo("RESTAURANTEADM")
        print()
        for numero, nombre in OPCIONES:
            print(f"{numero}. {nombre}")
        print()
    print(pintar("Siguiente paso: ", "celeste") + siguiente_paso(restaurante))


def abrir_modulo(opcion, funcion, *argumentos):
    """Limpia la pantalla, muestra la orientacion del modulo y lo abre."""
    limpiar()
    for linea in AYUDA_MODULO.get(opcion, []):
        info(linea)
    funcion(*argumentos)


def main():
    restaurante = Restaurante()
    mostrar_guia()
    mensaje = ""

    while True:
        mostrar_menu(restaurante)
        if mensaje:
            aviso(mensaje)
            mensaje = ""
        opcion = pedir("Opcion", "escriba el numero y Enter")

        if opcion == "1":
            abrir_modulo(opcion, cliente.menu, restaurante)
            pausa()   # Cliente vuelve enseguida: se espera para leer
        elif opcion == "2":
            abrir_modulo(opcion, mesa.menu, restaurante.mesas)
        elif opcion == "3":
            abrir_modulo(opcion, carta_menu.menu, restaurante)
        elif opcion == "4":
            abrir_modulo(opcion, mozo.menu, restaurante, restaurante.mesas)
        elif opcion == "5":
            pase.menu(restaurante)
        elif opcion == "6":
            abrir_modulo(opcion, caja.gestionar_caja, restaurante)
        elif opcion == "7":
            mostrar_guia()
        elif opcion == "0":
            limpiar()
            print("Hasta luego.")
            break
        else:
            mensaje = ("Opcion invalida. Escriba uno de los numeros del menu,"
                       " por ejemplo 2.")


if __name__ == "__main__":
    main()


def gestionar_caja(restaurante):
    """CAja recibe el objeto resaurante por parametro"""
    print("\n--- MÓDULO DE CAJA Y COBRANZA ---")
    print("1. Ver pedidos pendientes de cobro")
    print("2. Cobrar mesa / pedido")

    opcion_caja = input("Seleccione una opción de caja: ").strip()

    if opcion_caja == "1":
        print("\n[Caja] Consultando pedidos en curso...")

    elif opcion_caja == "2":
        mesa_id = input(
            "Ingrese el número de mesa o ID del cliente a cobrar: ")

        IVA = 0.10
        subtotal = 45000  # SUPONIENDO QUE ES EL TOTAL
        impuesto = subtotal * IVA
        total_a_pagar = subtotal + impuesto

        print(f"\n--- TICKET DE PAGO (Mesa {mesa_id}) ---")
        print(f"Subtotal: Gs. {subtotal:,.0f}")
        print(f"IVA (10%): Gs. {impuesto:,.0f}")
        print(f"TOTAL A PAGAR: Gs. {total_a_pagar:,.0f}")

        confirmar = input("¿Confirmar cobro? (s/n): ").lower()
        if confirmar == 's':
            print("¡Cobro exitoso! Comanda cerrada y guardada en el reporte de caja.")
        else:
            print("Cobro cancelado.")
    else:
        print("Opción de caja no válida.")
