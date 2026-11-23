from datetime import datetime

from modulos.base_datos import conexion
from modulos.entrada import (error, info, limpiar, ok, pausa, pedir,
                             pedir_texto, titulo)
from modulos.menu import obtener_carta


FORMATO_HORA = "%Y-%m-%d %H:%M:%S"

PENDIENTE = "pendiente"
EN_PREPARACION = "en preparacion"
LISTA = "lista"
ENTREGADA = "entregada"
COBRADA = "cobrada"


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
        """Lee de la base todas las comandas con sus platos."""
        with conexion() as con:
            filas = con.execute("SELECT numero, mesa, mozo, hora, estado FROM comandas"
                                " ORDER BY numero").fetchall()
            platos = con.execute("SELECT comanda, codigo, cantidad, obs FROM items"
                                 " ORDER BY id").fetchall()
        # Los platos se agrupan por numero de comanda para armar cada objeto Comanda
        por_comanda = {}
        for plato in platos:
            por_comanda.setdefault(plato["comanda"], []).append(
                {"codigo": plato["codigo"], "cantidad": plato["cantidad"], "obs": plato["obs"]})
        self.comandas = [
            Comanda.desde_diccionario({**dict(fila), "items": por_comanda.get(fila["numero"], [])})
            for fila in filas]

    def guardar(self, comanda=None):
        """Guarda una comanda puntual o, si no se indica ninguna, todas."""
        comandas = [comanda] if comanda else self.comandas
        with conexion() as con:
            for c in comandas:
                datos = c.a_diccionario()
                con.execute(
                    """INSERT INTO comandas (numero, mesa, mozo, hora, estado) VALUES (?, ?, ?, ?, ?)
                       ON CONFLICT(numero) DO UPDATE SET mesa = excluded.mesa, mozo = excluded.mozo,
                           hora = excluded.hora, estado = excluded.estado""",
                    (datos["numero"], datos["mesa"], datos["mozo"], datos["hora"], datos["estado"]))
                # Los platos de la comanda se reemplazan enteros por la version actual
                con.execute("DELETE FROM items WHERE comanda = ?", (c.numero,))
                con.executemany(
                    "INSERT INTO items (comanda, codigo, cantidad, obs) VALUES (?, ?, ?, ?)",
                    [(c.numero, i["codigo"], i["cantidad"], i["obs"]) for i in c.items])

    def nueva_comanda(self, mesa):
        # El numero sale de la base y no de la lista en memoria, por si otro modulo
        # o la interfaz web abrio una comanda mientras tanto
        with conexion() as con:
            ultimo = con.execute("SELECT COALESCE(MAX(numero), 0) FROM comandas").fetchone()[0]
        comanda = Comanda(ultimo + 1, mesa, self.nombre)
        self.comandas.append(comanda)
        self.guardar(comanda)
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
        self.guardar(comanda)


def cargar_items(comanda, carta, mozo):
    """Muestra la carta y deja cargar platos hasta que se escriba 0."""
    carta.mostrar(solo_disponibles=True)
    while True:
        # pedir() muestra el ejemplo entre parentesis y lee sin colores
        codigo = pedir("Codigo del plato", "ej.: P1 o B2; 0 para terminar")
        if codigo == "0":
            break
        producto = carta.obtener(codigo)
        # Cada validacion que falla muestra un error en rojo con el motivo
        if producto is None:
            error("Ese código no está en la carta. Hay que escribir uno de los\n"
                  "que aparecen arriba, por ejemplo P1 o B2.")
            continue
        if not producto.disponible:
            error(f"{producto.nombre} está agotado, la cocina lo marcó como\n"
                  "no disponible. Hay que elegir otro plato.")
            continue
        texto = pedir(f"Cantidad de '{producto.nombre}'",
                      "entero de 1 o más, Enter = 1") or "1"
        if not texto.isdigit() or int(texto) < 1:
            error("La cantidad tiene que ser un número entero de 1 o más,\n"
                  "escrito sin letras ni decimales.")
            continue
        comanda.agregar_item(producto.codigo, int(texto),
                             pedir("Observacion", "ej.: sin cebolla; Enter si no hay"))
        ok(f"{texto} x {producto.nombre} agregado a la comanda.")
    mozo.guardar(comanda)


def elegir_comanda(mozo, estado, carta):
    """Lista las comandas de un estado y devuelve la que el mozo elija."""
    comandas = mozo.por_estado(estado)
    if not comandas:
        error(f"No hay comandas en estado '{estado}'.")
        return None
    for comanda in comandas:
        print(f"  #{comanda.numero} Mesa {comanda.mesa}"
              f" - {comanda.calcular_total(carta):,} Gs.")
    texto = pedir("Numero de comanda", "uno de los numeros de arriba, ej.: 1")
    if not texto.isdigit():
        error("Hay que escribir el número de una de las comandas de arriba,\n"
              "usando solo dígitos.")
        return None
    elegida = mozo.buscar(int(texto))
    if elegida is None:
        error(f"No existe ninguna comanda con el número {texto}.")
        return None
    if elegida.estado != estado:
        error(f"La comanda #{elegida.numero} está en estado '{elegida.estado}'\n"
              f"y para esta operación tiene que estar en '{estado}'.")
        return None
    return elegida


# Orientacion que se muestra arriba del menu: que escribir en cada campo
AYUDA = [
    "MOZO: abra la comanda de una mesa, cargue los platos y enviela a cocina.",
    "Numero de mesa: una mesa ya registrada y ocupada, por ejemplo  1",
    "Codigo del plato: por ejemplo  P1 ; escriba  0  para terminar de cargar",
    "Observacion: texto libre, por ejemplo  sin cebolla  (o Enter si no hay)",
]


def menu(restaurante=None, mesas=None):
    # La carta y las mesas llegan del programa principal para que todos los
    # modulos trabajen sobre los mismos datos. Si no llegan mesas, el modulo
    # igual arranca pero no va a encontrar ninguna para atender.
    carta = obtener_carta(restaurante)
    mesas = mesas if mesas is not None else {}

    # El nombre del mozo se valida: solo letras y espacios, de 2 a 30 caracteres.
    # Si el usuario cancela con Enter vacio, se vuelve al menu principal.
    nombre = pedir_texto("Nombre del mozo", "Lucas", minimo=2, maximo=30,
                         solo_letras=True)
    if nombre is None:
        return
    mozo = Mozo(nombre)

    # 'esperar' vale True despues de ejecutar una opcion: asi, antes de limpiar
    # la pantalla, se espera un Enter para que el usuario alcance a leer el resultado.
    esperar = False

    while True:
        if esperar:
            pausa()
        limpiar()   # pantalla limpia en cada vuelta: la terminal no se llena de texto
        titulo(f"MODULO MOZO  ({mozo.nombre})")
        for linea in AYUDA:
            info(linea)
        print("1. Abrir comanda")
        print("2. Agregar platos a una comanda")
        print("3. Enviar comanda a la cocina")
        print("4. Entregar comanda lista")
        print("5. Ver todas las comandas")
        print("0. Volver")
        opcion = pedir("Opcion", "escriba el numero y Enter, ej.: 1")
        esperar = True
        print()

        if opcion == "1":
            if not mesas:
                error("No hay mesas registradas. Primero hay que darlas de"
                      " alta desde el modulo Mesa.")
                continue

            texto = pedir("Numero de mesa", "entero mayor que cero, ej.: 1")
            if not texto.isdigit() or int(texto) <= 0:
                error("El número de mesa tiene que ser un entero mayor que cero,\n"
                      "escrito solo con dígitos.")
                continue

            # Una comanda solo se abre sobre una mesa que exista y que ya haya
            # sido ocupada desde el modulo Mesa
            numero = int(texto)
            mesa = mesas.get(numero)
            if mesa is None:
                error(f"La mesa {numero} no está registrada. Hay que darla de alta\n"
                      "desde el módulo Mesa antes de poder atenderla.")
                continue
            if mesa.estado != "Ocupada":
                error(f"La mesa {numero} figura como Libre. Hay que ocuparla desde\n"
                      "el módulo Mesa antes de tomarle el pedido.")
                continue

            # Cada mesa puede tener una sola comanda activa a la vez, asi que se
            # revisa si ya hay alguna sin entregar antes de abrir otra
            comanda_activa = False
            for comanda_existente in mozo.comandas:
                if (comanda_existente.mesa == numero
                        and comanda_existente.estado not in (ENTREGADA, COBRADA)):
                    comanda_activa = True
                    break
            if comanda_activa:
                error(f"La mesa {numero} ya tiene una comanda sin entregar. Hay que\n"
                      "entregarla antes de abrir otra, o agregar los platos a esa.")
                continue

            comanda = mozo.nueva_comanda(numero)
            ok(f"Comanda #{comanda.numero} abierta.")
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
                error("La comanda no tiene ningún plato cargado todavía. Hay que\n"
                      "agregarlos con la opción 2 antes de mandarla a la cocina.")
            elif comanda:
                mozo.cambiar_estado(comanda, EN_PREPARACION)
                ok(f"Comanda #{comanda.numero} enviada a la cocina.")

        elif opcion == "4":
            comanda = elegir_comanda(mozo, LISTA, carta)
            if comanda:
                mozo.cambiar_estado(comanda, ENTREGADA)
                ok(f"Comanda #{comanda.numero} entregada en la mesa"
                   f" {comanda.mesa}. Total: {comanda.calcular_total(carta):,} Gs.")

        elif opcion == "5":
            if not mozo.comandas:
                info("Todavía no hay comandas.")
            for comanda in mozo.comandas:
                comanda.mostrar_informacion(carta)

        elif opcion == "0":
            break   # vuelve al menu principal sin esperar Enter

        else:
            # Cualquier otra cosa no es una opcion del menu
            error(f"'{opcion}' no es una opción del menú. Escriba uno de los\n"
                  "números de la lista, por ejemplo 1.")
