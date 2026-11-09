"""restauranteadm: punto de entrada y menú principal de la consola."""

from modelos import Restaurante
from modulos import caja, cliente, mesa, mozo, pass_ as pase

OPCIONES = {
    "1": ("Cliente (llegada y carta)", cliente.menu),
    "2": ("Mesa", mesa.menu),
    "3": ("Mozo (comandas)", mozo.menu),
    "4": ("Pass (cocina)", pase.menu),
    "5": ("Caja", caja.menu),
}


def main():
    restaurante = Restaurante()
    while True:
        print("\n=== RESTAURANTEADM ===")
        for clave, (titulo, _) in OPCIONES.items():
            print(f"{clave}. {titulo}")
        print("0. Salir")
        opcion = input("Opción: ").strip()
        if opcion == "0":
            break
        if opcion in OPCIONES:
            OPCIONES[opcion][1](restaurante)
        else:
            print("Opción inválida.")


if __name__ == "__main__":
    main()