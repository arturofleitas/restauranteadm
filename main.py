from collections import deque
from datetime import datetime, timedelta


# =====================================================================
# DATOS COMPARTIDOS (los edita una sola persona; avisar al grupo)
# =====================================================================
# carta: codigo -> {"nombre", "precio" en Gs. con IVA incluido, "disponible"}
carta = {
    "P1": {"nombre": "Milanesa con papas", "precio": 45000, "disponible": True},
    "P2": {"nombre": "Sopa paraguaya", "precio": 15000, "disponible": True},
    "P3": {"nombre": "Bife koygua", "precio": 55000, "disponible": True},
    "B1": {"nombre": "Jugo de naranja", "precio": 12000, "disponible": True},
}
mesas = {}             # numero de mesa -> datos de la mesa
lista_espera = deque() # clientes esperando mesa
cola_pass = deque()    # comandas pendientes (el mozo agrega con append)
en_preparacion = []    # comandas que cocina esta preparando
listas = []            # comandas terminadas (el mozo las retira de aqui)

# Una comanda es un diccionario:
#   {"numero": 1, "mesa": 3, "mozo": "Lucas", "hora": datetime,
#    "items": [{"codigo": "P1", "cantidad": 2, "obs": "sin cebolla"}],
#    "estado": "pendiente"}
# Estados: pendiente -> en preparacion -> lista -> entregada


# =====================================================================
# MODULO CLIENTE - Rama: cliente
# =====================================================================
def menu_cliente():
    print("\n[Cliente] Modulo en construccion.")


# =====================================================================
# FIN MODULO CLIENTE
# =====================================================================


# =====================================================================
# MODULO MESA - Rama: mesa
# =====================================================================
def menu_mesa():
    print("\n[Mesa] Modulo en construccion.")


# =====================================================================
# FIN MODULO MESA
# =====================================================================


# =====================================================================
# MODULO MOZO - Rama: mozo
# =====================================================================
def menu_mozo():
    print("\n[Mozo] Modulo en construccion.")


# =====================================================================
# FIN MODULO MOZO
# =====================================================================


# =====================================================================
# MODULO PASS (pase de cocina) - Responsable: Arturo - Rama: pass
# =====================================================================
# El pass recibe las comandas que envia el mozo, las prepara en orden
# de llegada y avisa cuando estan listas para que el mozo las retire.


def pass_minutos_espera(comanda):
    """Minutos transcurridos desde que el mozo cargo la comanda."""
    segundos = (datetime.now() - comanda["hora"]).total_seconds()
    return int(segundos // 60)


def pass_ordenar_por_espera(comandas):
    """Ordenamiento por insercion: la comanda mas antigua queda primera."""
    ordenadas = list(comandas)
    for i in range(1, len(ordenadas)):
        actual = ordenadas[i]
        j = i - 1
        while j >= 0 and ordenadas[j]["hora"] > actual["hora"]:
            ordenadas[j + 1] = ordenadas[j]
            j -= 1
        ordenadas[j + 1] = actual
    return ordenadas


def pass_mostrar_comanda(comanda, carta):
    """Imprime una comanda con sus platos y observaciones."""
    print(f"  Comanda #{comanda['numero']} | Mesa {comanda['mesa']} | "
          f"Mozo: {comanda['mozo']} | Espera: {pass_minutos_espera(comanda)} min")
    for item in comanda["items"]:
        plato = carta.get(item["codigo"])
        nombre = plato["nombre"] if plato else item["codigo"]
        linea = f"      {item['cantidad']} x {nombre}"
        if item.get("obs"):
            linea += f"  ({item['obs']})"
        print(linea)


def pass_ver_tablero(carta, cola_pass, en_preparacion, listas):
    """Muestra las tres columnas del pass: pendientes, en preparacion y listas."""
    print("\n--- PENDIENTES (en orden de llegada) ---")
    if not cola_pass:
        print("  No hay comandas pendientes.")
    for comanda in cola_pass:
        pass_mostrar_comanda(comanda, carta)

    print("\n--- EN PREPARACION (la mas antigua primero) ---")
    if not en_preparacion:
        print("  No hay comandas en preparacion.")
    for comanda in pass_ordenar_por_espera(en_preparacion):
        pass_mostrar_comanda(comanda, carta)

    print("\n--- LISTAS PARA RETIRAR ---")
    if not listas:
        print("  No hay comandas listas.")
    for comanda in listas:
        pass_mostrar_comanda(comanda, carta)


def pass_tomar_siguiente(cola_pass, en_preparacion):
    """Saca la primera comanda de la cola (FIFO) y la pasa a preparacion."""
    if not cola_pass:
        print("No hay comandas pendientes.")
        return None
    comanda = cola_pass.popleft()
    comanda["estado"] = "en preparacion"
    en_preparacion.append(comanda)
    print(f"Comanda #{comanda['numero']} (mesa {comanda['mesa']}) en preparacion.")
    return comanda


def pass_buscar_por_numero(comandas, numero):
    """Busqueda lineal de una comanda por su numero. Devuelve None si no esta."""
    for comanda in comandas:
        if comanda["numero"] == numero:
            return comanda
    return None


def pass_marcar_lista(en_preparacion, listas):
    """Pasa una comanda de 'en preparacion' a 'lista'."""
    if not en_preparacion:
        print("No hay comandas en preparacion.")
        return None
    texto = input("Numero de comanda terminada: ").strip()
    if not texto.isdigit():
        print("Debe ingresar un numero.")
        return None
    comanda = pass_buscar_por_numero(en_preparacion, int(texto))
    if comanda is None:
        print("Esa comanda no esta en preparacion.")
        return None
    en_preparacion.remove(comanda)
    comanda["estado"] = "lista"
    comanda["hora_lista"] = datetime.now()
    listas.append(comanda)
    print(f"Comanda #{comanda['numero']} LISTA. Avisar al mozo {comanda['mozo']} "
          f"(mesa {comanda['mesa']}).")
    return comanda


def pass_cambiar_disponibilidad(carta):
    """Cocina marca un plato como agotado o disponible de nuevo."""
    print("\nCodigo | Plato | Estado")
    for codigo, plato in carta.items():
        estado = "disponible" if plato["disponible"] else "AGOTADO"
        print(f"  {codigo} | {plato['nombre']} | {estado}")
    codigo = input("Codigo del plato a cambiar (Enter para cancelar): ").strip().upper()
    if codigo == "":
        return
    if codigo not in carta:
        print("Codigo inexistente.")
        return
    carta[codigo]["disponible"] = not carta[codigo]["disponible"]
    estado = "disponible" if carta[codigo]["disponible"] else "AGOTADO"
    print(f"{carta[codigo]['nombre']} ahora esta {estado}.")


def menu_pass(carta, cola_pass, en_preparacion, listas):
    """Submenu del pass. Se llama desde el menu principal."""
    while True:
        print("\n=== PASS (COCINA) ===")
        print(f"Pendientes: {len(cola_pass)} | En preparacion: {len(en_preparacion)} "
              f"| Listas: {len(listas)}")
        print("1. Ver tablero de comandas")
        print("2. Tomar siguiente comanda")
        print("3. Marcar comanda como lista")
        print("4. Cambiar disponibilidad de un plato")
        print("9. Cargar comandas de prueba (temporal)")
        print("0. Volver")
        opcion = input("Opcion: ").strip()
        if opcion == "1":
            pass_ver_tablero(carta, cola_pass, en_preparacion, listas)
        elif opcion == "2":
            pass_tomar_siguiente(cola_pass, en_preparacion)
        elif opcion == "3":
            pass_marcar_lista(en_preparacion, listas)
        elif opcion == "4":
            pass_cambiar_disponibilidad(carta)
        elif opcion == "9":
            pass_cargar_prueba(cola_pass)
        elif opcion == "0":
            break
        else:
            print("Opcion invalida.")


def pass_cargar_prueba(cola_pass):
    """TEMPORAL: carga 3 comandas de ejemplo. Borrar cuando el modulo Mozo
    ya envie comandas reales al pass."""
    ahora = datetime.now()
    cola_pass.append({
        "numero": 1, "mesa": 3, "mozo": "Lucas", "hora": ahora - timedelta(minutes=12),
        "items": [{"codigo": "P1", "cantidad": 2, "obs": "sin cebolla"},
                  {"codigo": "B1", "cantidad": 2, "obs": ""}],
        "estado": "pendiente",
    })
    cola_pass.append({
        "numero": 2, "mesa": 5, "mozo": "Lucia", "hora": ahora - timedelta(minutes=7),
        "items": [{"codigo": "P3", "cantidad": 1, "obs": "bien cocido"}],
        "estado": "pendiente",
    })
    cola_pass.append({
        "numero": 3, "mesa": 1, "mozo": "Lucas", "hora": ahora - timedelta(minutes=2),
        "items": [{"codigo": "P2", "cantidad": 4, "obs": ""}],
        "estado": "pendiente",
    })
    print("Se cargaron 3 comandas de prueba.")


# =====================================================================
# FIN MODULO PASS
# =====================================================================


# =====================================================================
# MODULO CAJA - Rama: caja
# =====================================================================
def menu_caja():
    print("\n[Caja] Modulo en construccion.")


# =====================================================================
# FIN MODULO CAJA
# =====================================================================


# =====================================================================
# MENU PRINCIPAL (lo edita una sola persona; avisar al grupo)
# =====================================================================
def main():
    while True:
        print("\n=== RESTAURANTEADM ===")
        print("1. Cliente (llegada y carta)")
        print("2. Mesa")
        print("3. Mozo (comandas)")
        print("4. Pass (cocina)")
        print("5. Caja")
        print("0. Salir")
        opcion = input("Opcion: ").strip()
        if opcion == "1":
            menu_cliente()
        elif opcion == "2":
            menu_mesa()
        elif opcion == "3":
            menu_mozo()
        elif opcion == "4":
            menu_pass(carta, cola_pass, en_preparacion, listas)
        elif opcion == "5":
            menu_caja()
        elif opcion == "0":
            break
        else:
            print("Opcion invalida.")


if __name__ == "__main__":
    main()