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
