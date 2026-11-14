"""Módulo para la gestión de caja y cobranza de mesas."""
from modulos.mozo import ENTREGADA, Mozo


def gestionar_caja(restaurante):
    """Caja recibe el objeto restaurante por parámetro."""
    while True:
        print("\n--- MÓDULO DE CAJA Y COBRANZA ---")
        print("1. Ver pedidos pendientes de cobro")
        print("2. Cobrar mesa / pedido")
        print("0. Volver al menú principal")

        opcion_caja = input("\nSeleccione una opción de caja: ").strip()

        if opcion_caja == "0":
            break

        elif opcion_caja == "1":
            print("\n[Caja] Consultando pedidos en curso...")
            registro = Mozo("Caja")
            pendientes = registro.por_estado(ENTREGADA)

            if not pendientes:
                print("  No hay pedidos pendientes de cobro en este momento.")
            else:
                print(
                    f"\n  Hay {len(pendientes)} pedido(s) listos para cobrar:")
                for comanda in pendientes:
                    total = comanda.calcular_total(restaurante.carta)
                    print(
                        f"  - Mesa {comanda.mesa} | Comanda #{comanda.numero} | Mozo: {comanda.mozo} | Total: Gs. {total:,.0f}")

        elif opcion_caja == "2":
            registro = Mozo("Caja")
            pendientes = registro.por_estado(ENTREGADA)

            if not pendientes:
                print("\n  No hay pedidos entregados pendientes de cobro.")
                continue

            mesa_id = input(
                "\nIngrese el número de mesa o ID del cliente a cobrar: ").strip()

            if not mesa_id.isdigit():
                print("  Debe ingresar un número de mesa válido.")
                continue

            num_mesa = int(mesa_id)

            comandas_mesa = [c for c in pendientes if c.mesa == num_mesa]

            if not comandas_mesa:
                print(
                    f"  No se encontraron comandas pendientes de cobro para la mesa {num_mesa}.")
                continue

            subtotal = sum(c.calcular_total(restaurante.carta)
                           for c in comandas_mesa)

            IVA = 0.10
            impuesto = subtotal * IVA
            total_a_pagar = subtotal + impuesto

            print(f"\n--- TICKET DE PAGO (Mesa {num_mesa}) ---")
            for c in comandas_mesa:
                print(f"Comanda #{c.numero}:")
                for item in c.items:
                    prod = restaurante.carta.obtener(item["codigo"])
                    nombre = prod.nombre if prod else item["codigo"]
                    p_unit = prod.precio if prod else 0
                    print(
                        f"  {item['cantidad']}x {nombre:<20} Gs. {p_unit * item['cantidad']:,.0f}")

            print("-" * 40)
            print(f"Subtotal:      Gs. {subtotal:,.0f}")
            print(f"IVA (10%):     Gs. {impuesto:,.0f}")
            print(f"TOTAL A PAGAR: Gs. {total_a_pagar:,.0f}")
            print("-" * 40)

            confirmar = input("¿Confirmar cobro? (s/n): ").strip().lower()
            if confirmar == "s":

                for c in comandas_mesa:
                    registro.cambiar_estado(c, "cobrada")

                if num_mesa in restaurante.mesas:
                    restaurante.mesas[num_mesa].liberar()

                print(
                    f"\n¡Cobro exitoso! Mesa {num_mesa} cobrada y liberada correctamente.")
            else:
                print("\nCobro cancelado.")

        else:
            print("Opción de caja no válida.")
