"""Modulo para gestionar las mesas del restaurante."""

from modulos.entrada import (aviso, error, info, limpiar, mostrar_mensaje, ok,
                             pausa, pedir_entero, pedir_opcion, pintar, titulo)

MAX_NUMERO_MESA = 99      # numeros de mesa permitidos: 1 a 99
MAX_CAPACIDAD = 20        # personas por mesa: 1 a 20
POR_FILA = 6              # mesas por fila al listar (la lista no crece a lo largo)


class Mesa:

    # Constructor: guarda los datos de cada mesa.
    def __init__(self, numero, capacidad):
        self.numero = numero
        self.capacidad = capacidad
        self.estado = "Libre"

    # Cambia el estado de la mesa a ocupada.
    def ocupar(self):
        if self.estado == "Libre":
            self.estado = "Ocupada"
            return True
        return False

    # Cambia el estado de la mesa a libre.
    def liberar(self):
        if self.estado == "Ocupada":
            self.estado = "Libre"
            return True
        return False

    # Muestra la informacion de la mesa.
    def mostrar(self):
        print(f"Mesa {self.numero} | Capacidad: {self.capacidad} | Estado: {self.estado}")


def resumen(mesas):
    """Una sola linea con el estado general, sin importar cuantas mesas haya."""
    libres = sum(1 for m in mesas.values() if m.estado == "Libre")
    return (f"Mesas: {len(mesas)}   "
            f"{pintar('Libres: ' + str(libres), 'verde')}   "
            f"{pintar('Ocupadas: ' + str(len(mesas) - libres), 'rojo')}")


def mostrar_cuadricula(mesas, solo_libres=False):
    """Dibuja las mesas en filas de POR_FILA: verde = libre, rojo = ocupada.

    Asi 5 mesas o 100 mesas ocupan poco espacio en pantalla."""
    elegidas = [m for _, m in sorted(mesas.items())
                if not solo_libres or m.estado == "Libre"]
    if not elegidas:
        aviso("No hay mesas para mostrar.")
        return
    for i in range(0, len(elegidas), POR_FILA):
        fila = ""
        for m in elegidas[i:i + POR_FILA]:
            celda = f"Mesa {m.numero:>2} ({m.capacidad:>2}p)"
            fila += pintar(celda, "verde" if m.estado == "Libre" else "rojo") + "   "
        print(fila)
    info("verde = libre, rojo = ocupada, entre parentesis la capacidad en personas (p)")


def _pedir_mesa(mesas, etiqueta="Numero de la mesa"):
    """Pide el numero de una mesa YA registrada. Devuelve la Mesa o None si cancela."""
    while True:
        numero = pedir_entero(etiqueta, "1", 1, MAX_NUMERO_MESA)
        if numero is None:
            return None
        if numero in mesas:
            return mesas[numero]
        error(f"La mesa {numero} no esta registrada. Registradas: "
              + (", ".join(str(n) for n in sorted(mesas)) or "ninguna") + ".")


AYUDA = [
    "MESAS: registre las mesas del local y marquelas ocupadas o libres.",
    f"Numero de mesa: entero de 1 a {MAX_NUMERO_MESA}, por ejemplo  1",
    f"Capacidad: cantidad de personas, de 1 a {MAX_CAPACIDAD}, por ejemplo  4",
    "Una mesa debe estar OCUPADA para que el mozo pueda tomarle el pedido.",
]


# Menu principal del modulo Mesa.
# Recibe las mesas compartidas por el programa principal.
def menu(mesas):
    mensaje = None   # resultado de la accion anterior, se muestra arriba de la pantalla nueva

    while True:
        limpiar()
        titulo("GESTION DE MESAS")
        for linea in AYUDA:
            info(linea)
        print()
        print(resumen(mesas))
        print()
        print("1. Registrar mesa")
        print("2. Consultar mesas")
        print("3. Ocupar mesa")
        print("4. Liberar mesa")
        print("5. Consultar mesas disponibles")
        print("0. Volver al menu principal")
        print()
        mostrar_mensaje(mensaje)
        mensaje = None

        opcion = pedir_opcion("Opcion", "012345", "1")

        if opcion == "1":
            numero = pedir_entero("Numero de mesa", "1", 1, MAX_NUMERO_MESA)
            if numero is None:
                continue
            if numero in mesas:
                mensaje = ("error", f"La mesa {numero} ya esta registrada.")
                continue
            capacidad = pedir_entero("Capacidad de personas", "4", 1, MAX_CAPACIDAD)
            if capacidad is None:
                continue
            mesas[numero] = Mesa(numero, capacidad)
            mensaje = ("ok", f"Mesa {numero} registrada (capacidad {capacidad}).")

        elif opcion in ("2", "5"):
            print()
            if not mesas:
                aviso("No hay mesas registradas. Use la opcion 1.")
            else:
                print(resumen(mesas))
                print()
                mostrar_cuadricula(mesas, solo_libres=(opcion == "5"))
            pausa()

        elif opcion in ("3", "4"):
            if not mesas:
                mensaje = ("error", "No hay mesas registradas. Use primero la opcion 1.")
                continue
            print()
            mostrar_cuadricula(mesas)
            print()
            m = _pedir_mesa(mesas)
            if m is None:
                continue
            if opcion == "3":
                if m.ocupar():
                    mensaje = ("ok", f"Mesa {m.numero} ocupada.")
                else:
                    mensaje = ("error", f"La mesa {m.numero} ya esta ocupada.")
            else:
                if m.liberar():
                    mensaje = ("ok", f"Mesa {m.numero} liberada.")
                else:
                    mensaje = ("error", f"La mesa {m.numero} ya esta libre.")

        elif opcion == "0":
            break


# Permite probar el modulo independientemente.
if __name__ == "__main__":
    mesas = {}
    menu(mesas)
