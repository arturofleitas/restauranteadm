"""restauranteadm: sistema de restaurante con comandas y cobro digital.

main.py solo crea los datos compartidos y muestra el menu principal.
Cada modulo vive en su propio archivo dentro de la carpeta modulos/."""

from modulos import cliente, mesa, mozo
from modulos import menu as carta_menu
from modulos import pass_ as pase
from modulos.menu import Carta


class Restaurante:
    """Datos que comparten todos los modulos durante la ejecucion."""

    def __init__(self):
        self.carta = Carta()
        self.mesas = {}
        self.clientes = {}

def main():
    restaurante = Restaurante()

    while True:
        print("\n=== RESTAURANTEADM ===")
        print("1. Cliente")
        print("2. Mesa")
        print("3. Menu (carta)")
        print("4. Mozo (comandas)")
        print("5. Pass (cocina)")
        print("6. Caja")
        print("0. Salir")
        opcion = input("Opcion: ").strip()

        if opcion == "1":
            cliente.menu(restaurante)
        elif opcion == "2":
            mesa.menu(restaurante.mesas)
        elif opcion == "3":
            carta_menu.menu(restaurante)
        elif opcion == "4":
            mozo.menu(restaurante, restaurante.mesas)
        elif opcion == "5":
            pase.menu(restaurante)
        elif opcion == "6":
            print("\n[Caja] Modulo en construccion.")
        elif opcion == "0":
            break
        else:
            print("Opcion invalida.")


if __name__ == "__main__":
    main()