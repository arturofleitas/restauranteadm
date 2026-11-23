"""Módulo para la gestión de caja y cobranza de mesas."""
from modulos.entrada import (aviso, error, info, limpiar, ok, pausa, pedir,
                             pedir_si_no, titulo)
from modulos.base_datos import registrar_venta
from modulos.mozo import COBRADA, ENTREGADA, Mozo

IVA = 0.10


def calcular_cuenta(comandas, carta):
    """Devuelve subtotal, IVA y total de las comandas de una mesa."""
    subtotal = sum(c.calcular_total(carta) for c in comandas)
    impuesto = subtotal * IVA
    return subtotal, impuesto, subtotal + impuesto


def cerrar_cuenta(num_mesa, comandas, registro, mesas, carta):
    """Marca las comandas como cobradas, libera la mesa y registra la venta.

    La usan tanto la caja de consola como la interfaz web, asi el cobro se hace
    siempre de la misma forma.
    """
    subtotal, impuesto, total = calcular_cuenta(comandas, carta)
    for c in comandas:
        registro.cambiar_estado(c, COBRADA)
    # Al cobrar, la mesa vuelve a quedar libre para el proximo cliente
    if num_mesa in mesas:
        mesas[num_mesa].liberar()
    registrar_venta(num_mesa, [c.numero for c in comandas], subtotal, impuesto, total)
    return total


def gestionar_caja(restaurante):
    """Caja recibe el objeto restaurante por parámetro."""
    # 'esperar' vale True despues de ejecutar una opcion: antes de limpiar la
    # pantalla se espera un Enter para que el usuario alcance a leer el resultado.
    esperar = False

    while True:
        if esperar:
            pausa()
        limpiar()   # pantalla limpia en cada vuelta: la terminal no se llena de texto
        titulo("MÓDULO DE CAJA Y COBRANZA")
        info("Numero de mesa: el de una mesa con pedidos entregados, ej.: 1")
        print("1. Ver pedidos pendientes de cobro")
        print("2. Cobrar mesa / pedido")
        print("0. Volver al menú principal")

        opcion_caja = pedir("Opcion", "escriba el numero y Enter, ej.: 1")
        esperar = True
        print()

        if opcion_caja == "0":
            break   # vuelve al menu principal sin esperar Enter

        elif opcion_caja == "1":
            # Las comandas ENTREGADAS son las que ya se sirvieron y faltan cobrar
            registro = Mozo("Caja")
            pendientes = registro.por_estado(ENTREGADA)

            if not pendientes:
                aviso("No hay pedidos pendientes de cobro en este momento.")
            else:
                print(f"Hay {len(pendientes)} pedido(s) listos para cobrar:")
                for comanda in pendientes:
                    total = comanda.calcular_total(restaurante.carta)
                    print(
                        f"  - Mesa {comanda.mesa} | Comanda #{comanda.numero} | Mozo: {comanda.mozo} | Total: Gs. {total:,.0f}")

        elif opcion_caja == "2":
            registro = Mozo("Caja")
            pendientes = registro.por_estado(ENTREGADA)

            if not pendientes:
                aviso("No hay pedidos entregados pendientes de cobro.")
                continue

            # Se muestran las mesas con algo para cobrar para que el usuario sepa que numero escribir
            mesas_con_deuda = sorted({c.mesa for c in pendientes})
            info("Mesas con cuenta para cobrar: " + ", ".join(str(m) for m in mesas_con_deuda))
            mesa_id = pedir("Numero de mesa a cobrar", "ej.: " + str(mesas_con_deuda[0]))

            # Validacion: solo digitos (evita letras, vacios y numeros negativos)
            if not mesa_id.isdigit():
                error("Debe ingresar un número de mesa válido: solo dígitos,\n"
                      "por ejemplo 1.")
                continue

            num_mesa = int(mesa_id)

            comandas_mesa = [c for c in pendientes if c.mesa == num_mesa]

            if not comandas_mesa:
                error(f"No se encontraron comandas pendientes de cobro para la mesa {num_mesa}.\n"
                      "Elija una de las mesas indicadas arriba.")
                continue

            subtotal, impuesto, total_a_pagar = calcular_cuenta(comandas_mesa, restaurante.carta)

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

            # pedir_si_no repite la pregunta en rojo hasta que respondan s o n
            if pedir_si_no("¿Confirmar cobro?"):

                cerrar_cuenta(num_mesa, comandas_mesa, registro,
                              restaurante.mesas, restaurante.carta)

                ok(f"¡Cobro exitoso! Mesa {num_mesa} cobrada y liberada correctamente.")
            else:
                aviso("Cobro cancelado.")

        else:
            # Cualquier otra cosa no es una opcion del menu
            error(f"'{opcion_caja}' no es una opción de caja. Escriba uno de los\n"
                  "números de la lista, por ejemplo 1.")
