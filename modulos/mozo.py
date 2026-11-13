import json
import os
from datetime import datetime

from modulos.menu import obtener_carta

ARCHIVO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos", "comandas.json")

FORMATO_HORA = "%Y-%m-%d %H:%M:%S"

PENDIENTE = "pendiente"
EN_PREPARACION = "en preparacion"
LISTA = "lista"
ENTREGADA = "entregada"


class Comanda:

    def __init__(self, numero, mesa, mozo):
        self.numero = numero
        self.mesa = mesa
        self.mozo = mozo
        self.hora = datetime.now()
        self.items = []
        self.estado = PENDIENTE

    def agregar_item(self, codigo, cantidad, obs=""):
        """Suma un plato, acumulando la cantidad si ya estaba pedido igual."""
        for item in self.items:
            if item["codigo"] == codigo and item["obs"] == obs:
                item["cantidad"] += cantidad
                return
        self.items.append({"codigo": codigo, "cantidad": cantidad, "obs": obs})

    def calcular_total(self, carta):
        total = 0
        for item in self.items:
            producto = carta.obtener(item["codigo"])
            if producto:
                total += producto.precio * item["cantidad"]
        return total

    def minutos_de_espera(self):
        return int((datetime.now() - self.hora).total_seconds() // 60)

    def mostrar_informacion(self, carta):
        print(f"\n  Comanda #{self.numero} | Mesa {self.mesa} | Mozo: {self.mozo}")
        print(f"  {self.estado} | espera {self.minutos_de_espera()} min")
        for item in self.items:
            producto = carta.obtener(item["codigo"])
            nombre = producto.nombre if producto else item["codigo"]
            print(f"  {item['cantidad']:>2} x {nombre:<24}"
                  f" {(producto.precio * item['cantidad']) if producto else 0:>7,} Gs."
                  f"{'  (' + item['obs'] + ')' if item['obs'] else ''}")
        print(f"  TOTAL: {self.calcular_total(carta):,} Gs.")

    def a_diccionario(self):
        return {"numero": self.numero, "mesa": self.mesa, "mozo": self.mozo,
                "hora": self.hora.strftime(FORMATO_HORA),
                "items": self.items, "estado": self.estado}

    @staticmethod
    def desde_diccionario(datos):
        comanda = Comanda(datos["numero"], datos["mesa"], datos["mozo"])
        # La hora viaja como texto en el JSON y hay que volver a convertirla a fecha
        comanda.hora = datetime.strptime(datos["hora"], FORMATO_HORA)
        comanda.items = datos["items"]
        comanda.estado = datos["estado"]
        return comanda


class Mozo:

    def __init__(self, nombre="Sin nombre"):
        self.nombre = nombre
        self.comandas = []
        self.cargar()

    def cargar(self):
        """Lee las comandas del JSON, o empieza vacío si el archivo todavía no existe."""
        if not os.path.exists(ARCHIVO):
            return
        with open(ARCHIVO, encoding="utf-8") as archivo:
            self.comandas = [Comanda.desde_diccionario(d) for d in json.load(archivo)]

    def guardar(self):
        """Escribe todas las comandas en el JSON."""
        os.makedirs(os.path.dirname(ARCHIVO), exist_ok=True)
        with open(ARCHIVO, "w", encoding="utf-8") as archivo:
            # ensure_ascii en falso conserva las tildes legibles dentro del archivo
            json.dump([c.a_diccionario() for c in self.comandas], archivo,
                      indent=2, ensure_ascii=False)

    def nueva_comanda(self, mesa):
        numero = max([c.numero for c in self.comandas], default=0) + 1
        comanda = Comanda(numero, mesa, self.nombre)
        self.comandas.append(comanda)
        self.guardar()
        return comanda

    def buscar(self, numero):
        """Busca una comanda por su número con búsqueda lineal."""
        for comanda in self.comandas:
            if comanda.numero == numero:
                return comanda
        return None

    def por_estado(self, estado):
        return [c for c in self.comandas if c.estado == estado]

    def cambiar_estado(self, comanda, estado):
        comanda.estado = estado
        self.guardar()


def cargar_items(comanda, carta, mozo):
    """Muestra la carta y deja cargar platos hasta que se escriba 0."""
    carta.mostrar(solo_disponibles=True)
    while True:
        codigo = input("Código del plato (0 para terminar): ").strip()
        if codigo == "0":
            break
        producto = carta.obtener(codigo)
        if producto is None or not producto.disponible:
            print("  Ese plato no está disponible.")
            continue
        texto = input(f"  Cantidad de '{producto.nombre}': ").strip() or "1"
        if not texto.isdigit() or int(texto) < 1:
            print("  Cantidad inválida.")
            continue
        comanda.agregar_item(producto.codigo, int(texto),
                             input("  Observación (Enter si no hay): ").strip())
        print(f"  + {texto} x {producto.nombre}")
    mozo.guardar()


def elegir_comanda(mozo, estado, carta):
    """Lista las comandas de un estado y devuelve la que el mozo elija."""
    comandas = mozo.por_estado(estado)
    if not comandas:
        print(f"  No hay comandas en estado '{estado}'.")
        return None
    for comanda in comandas:
        print(f"  #{comanda.numero} Mesa {comanda.mesa}"
              f" - {comanda.calcular_total(carta):,} Gs.")
    texto = input("Número de comanda: ").strip()
    if not texto.isdigit():
        print("  Número inválido.")
        return None
    elegida = mozo.buscar(int(texto))
    if elegida is None or elegida.estado != estado:
        print("  Esa comanda no está disponible.")
        return None
    return elegida


def menu(restaurante=None, mesas=None):
    # La carta y las mesas llegan del programa principal para que todos los
    # modulos trabajen sobre los mismos datos. Si no llegan mesas, el modulo
    # igual arranca pero no va a encontrar ninguna para atender.
    carta = obtener_carta(restaurante)
    mesas = mesas if mesas is not None else {}
    mozo = Mozo(input("\nNombre del mozo: ").strip() or "Sin nombre")

    while True:
        print("\n=== MODULO MOZO ===")
        print("1. Abrir comanda")
        print("2. Agregar platos a una comanda")
        print("3. Enviar comanda a la cocina")
        print("4. Entregar comanda lista")
        print("5. Ver todas las comandas")
        print("0. Volver")
        opcion = input("Opción: ").strip()

        if opcion == "1":
            if not mesas:
                print("  No hay mesas registradas. Primero hay que darlas de"
                      " alta desde el modulo Mesa.")
                continue

            texto = input("Número de mesa: ").strip()
            if not texto.isdigit() or int(texto) <= 0:
                print("  Número de mesa inválido.")
                continue

            # Una comanda solo se abre sobre una mesa que exista y que ya haya
            # sido ocupada desde el modulo Mesa
            numero = int(texto)
            mesa = mesas.get(numero)
            if mesa is None:
                print("  La mesa no existe. Hay que registrarla primero.")
                continue
            if mesa.estado != "Ocupada":
                print("  La mesa está libre. Hay que ocuparla primero.")
                continue

            # Cada mesa puede tener una sola comanda activa a la vez, asi que se
            # revisa si ya hay alguna sin entregar antes de abrir otra
            comanda_activa = False
            for comanda_existente in mozo.comandas:
                if (comanda_existente.mesa == numero
                        and comanda_existente.estado != ENTREGADA):
                    comanda_activa = True
                    break
            if comanda_activa:
                print("  Esta mesa ya tiene una comanda activa.")
                continue

            comanda = mozo.nueva_comanda(numero)
            print(f"  Comanda #{comanda.numero} abierta.")
            cargar_items(comanda, carta, mozo)
            comanda.mostrar_informacion(carta)

        elif opcion == "2":
            comanda = elegir_comanda(mozo, PENDIENTE, carta)
            if comanda:
                cargar_items(comanda, carta, mozo)
                comanda.mostrar_informacion(carta)

        elif opcion == "3":
            comanda = elegir_comanda(mozo, PENDIENTE, carta)
            if comanda and not comanda.items:
                print("  No se puede enviar una comanda sin platos.")
            elif comanda:
                mozo.cambiar_estado(comanda, EN_PREPARACION)
                print(f"  Comanda #{comanda.numero} enviada a la cocina.")

        elif opcion == "4":
            comanda = elegir_comanda(mozo, LISTA, carta)
            if comanda:
                mozo.cambiar_estado(comanda, ENTREGADA)
                print(f"  Comanda #{comanda.numero} entregada en la mesa"
                      f" {comanda.mesa}. Total: {comanda.calcular_total(carta):,} Gs.")

        elif opcion == "5":
            if not mozo.comandas:
                print("  Todavía no hay comandas.")
            for comanda in mozo.comandas:
                comanda.mostrar_informacion(carta)

        elif opcion == "0":
            break
