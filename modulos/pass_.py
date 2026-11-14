"""El pass es el punto donde la cocina recibe las comandas que envia el mozo
y avisa cuando estan listas para llevar a la mesa.

Como se conecta con los otros modulos:
  - Mozo (opcion 3) deja la comanda en estado "en preparacion".
  - Pass muestra esas comandas en orden de llegada y las pasa a "lista".
  - Mozo (opcion 4) entrega las comandas que estan en "lista".
  - La carta es la misma que usan Menu y Mozo (un solo objeto Carta).

Las comandas se guardan en datos/comandas.json. Pass usa la misma clase
que el modulo Mozo para leer y escribir ese archivo, asi no hay dos copias.

El archivo se llama pass_.py porque 'pass' es palabra reservada de Python.
"""

import os
import sys
from collections import deque

from modulos.menu import obtener_carta
from modulos.mozo import EN_PREPARACION, LISTA, Mozo

# Minutos a partir de los cuales una comanda se marca como demorada
LIMITE_DEMORA = 20

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



class Pass:

    def __init__(self, carta):
        self.carta = carta
        self.registro = None     # acceso a las comandas guardadas en el JSON
        self.cola = deque()      # comandas en cocina, la mas antigua primero
        self.actualizar()

    # ---------- Datos y algoritmos ----------

    def actualizar(self):
        """Vuelve a leer las comandas y arma la cola de cocina."""
        self.registro = Mozo("Cocina")
        en_cocina = self.registro.por_estado(EN_PREPARACION)
        self.cola = deque(self.ordenar_por_hora(en_cocina))

    def ordenar_por_hora(self, comandas):
        """Ordenamiento por insercion: la comanda mas antigua queda primera."""
        ordenadas = list(comandas)
        for i in range(1, len(ordenadas)):
            actual = ordenadas[i]
            j = i - 1
            while j >= 0 and ordenadas[j].hora > actual.hora:
                ordenadas[j + 1] = ordenadas[j]
                j -= 1
            ordenadas[j + 1] = actual
        return ordenadas

    def buscar_en_cola(self, numero):
        """Busqueda lineal de una comanda de la cola por su numero."""
        for comanda in self.cola:
            if comanda.numero == numero:
                return comanda
        return None

    # ---------- Pantallas ----------

    def mostrar_comanda(self, comanda):
        """Muestra la comanda como la ve la cocina: platos y observaciones."""
        espera = comanda.minutos_de_espera()
        encabezado = (f"\n  Comanda #{comanda.numero} | Mesa {comanda.mesa} | "
                      f"Mozo: {comanda.mozo} | Espera: {espera} min")
        if espera >= LIMITE_DEMORA:
            print(pintar(encabezado + "  << DEMORADA", "rojo"))
        else:
            print(pintar(encabezado, "blanco"))
        for item in comanda.items:
            producto = self.carta.obtener(item["codigo"])
            nombre = producto.nombre if producto else item["codigo"]
            linea = f"    {item['cantidad']:>2} x {nombre}"
            if item.get("obs"):
                linea += pintar(f"  ({item['obs']})", "amarillo")
            print(linea)

    def ver_cola(self):
        """Lista las comandas en cocina, en el orden en que deben salir."""
        titulo("COMANDAS EN COCINA")
        info("Orden de salida: la mas antigua primero.")
        if not self.cola:
            aviso("No hay comandas en cocina. Llegan cuando el mozo usa"
                          " 'Enviar comanda a la cocina'.")
        for comanda in self.cola:
            self.mostrar_comanda(comanda)

    def ver_listas(self):
        """Lista las comandas terminadas que el mozo todavia no retiro."""
        titulo("LISTAS PARA RETIRAR")
        info("Comandas terminadas que el mozo todavia no entrego.")
        listas = self.ordenar_por_hora(self.registro.por_estado(LISTA))
        if not listas:
            aviso("No hay comandas esperando al mozo.")
        for comanda in listas:
            self.mostrar_comanda(comanda)

    def marcar_lista(self, comanda):
        """Saca la comanda de la cola y la deja en estado 'lista'."""
        self.cola.remove(comanda)
        self.registro.cambiar_estado(comanda, LISTA)
        ok(f"Comanda #{comanda.numero} LISTA. Avisar al mozo "
                   f"{comanda.mozo} (mesa {comanda.mesa}).")
        info("Siguiente paso: el mozo la entrega desde Mozo, opcion 4.")

    def despachar_siguiente(self):
        """Termina la primera comanda de la cola (la que mas espero)."""
        titulo("MARCAR LA SIGUIENTE COMANDA COMO LISTA")
        if not self.cola:
            aviso("No hay comandas en cocina.")
            return
        comanda = self.cola[0]
        info("Esta es la comanda que mas tiempo lleva esperando:")
        self.mostrar_comanda(comanda)
        print()
        if pedir("Ya esta terminada?", "s = si, n = no").lower() in ("s", "si"):
            self.marcar_lista(comanda)
        else:
            aviso("No se hicieron cambios.")

    def despachar_por_numero(self):
        """Termina una comanda puntual, aunque no sea la primera de la cola."""
        titulo("MARCAR UNA COMANDA POR NUMERO")
        if not self.cola:
            aviso("No hay comandas en cocina.")
            return
        info("Comandas en cocina:")
        for comanda in self.cola:
            print(f"  #{comanda.numero}  Mesa {comanda.mesa}"
                  f"  - espera {comanda.minutos_de_espera()} min")
        print()
        ejemplo = str(self.cola[0].numero)
        texto = pedir("Numero de comanda terminada", "ej.: " + ejemplo)
        if not texto.isdigit():
            error("Hay que escribir solo el numero de la comanda, por"
                          f" ejemplo {ejemplo}. No lleva letras ni el simbolo #.")
            return
        comanda = self.buscar_en_cola(int(texto))
        if comanda is None:
            error(f"La comanda {texto} no esta en cocina. Elija un"
                          " numero de la lista de arriba.")
            return
        self.marcar_lista(comanda)

    def cambiar_disponibilidad(self):
        """La cocina avisa que un plato se agoto o que vuelve a estar disponible."""
        titulo("MARCAR PLATO AGOTADO O DISPONIBLE")
        self.carta.mostrar()
        print()
        info("El codigo es la letra y el numero de la primera columna.")
        codigo = pedir("Codigo del plato", "ej.: P1 o B2; Enter para cancelar")
        if codigo == "":
            aviso("No se hicieron cambios.")
            return
        producto = self.carta.cambiar_disponibilidad(codigo)
        if producto is None:
            error(f"El codigo '{codigo}' no esta en la carta. Use uno"
                          " de la lista, por ejemplo P1.")
        elif producto.disponible:
            ok(f"{producto.nombre} vuelve a estar DISPONIBLE.")
        else:
            ok(f"{producto.nombre} quedo AGOTADO. El mozo ya no puede"
                       " cargarlo en una comanda.")

    # ---------- Submenu ----------

    def menu(self):
        while True:
            self.actualizar()
            listas = len(self.registro.por_estado(LISTA))
            limpiar()
            titulo("MODULO PASS (COCINA)")
            info("Aqui la cocina ve los pedidos que envio el mozo y"
                         " avisa cuando estan listos.")
            print(f"\nEn cocina: {pintar(str(len(self.cola)), 'amarillo')}"
                  f"   |   Listas para retirar: "
                  f"{pintar(str(listas), 'verde')}\n")
            print("1. Ver comandas en cocina")
            print("2. Marcar la siguiente comanda como lista")
            print("3. Marcar una comanda por numero como lista")
            print("4. Ver comandas listas para retirar")
            print("5. Marcar plato agotado o disponible")
            print("0. Volver al menu principal\n")
            opcion = pedir("Opcion", "0 a 5")

            acciones = {
                "1": self.ver_cola,
                "2": self.despachar_siguiente,
                "3": self.despachar_por_numero,
                "4": self.ver_listas,
                "5": self.cambiar_disponibilidad,
            }
            if opcion == "0":
                break
            limpiar()
            if opcion in acciones:
                acciones[opcion]()
            else:
                error("Opcion invalida. Escriba un numero del 0 al 5.")
            pausa()


def menu(restaurante=None):
    """Entrada del modulo, con la misma forma que usan Menu y Mozo."""
    Pass(obtener_carta(restaurante)).menu()


# Permite probar el modulo por separado: python -m modulos.pass_
if __name__ == "__main__":
    menu()