from modulos.base_datos import conexion
from modulos.entrada import (error, info, limpiar, ok, pausa, pedir,
                             pedir_entero, titulo)


INICIALES = {
    "P1": ("Pizza Napolitana", 60000),
    "P2": ("Hamburguesa clásica", 35000),
    "P3": ("Lasaña", 52000),
    "P4": ("Milanesa con papas", 50000),
    "P5": ("Lomito completo", 55000),
    "P6": ("Sopa paraguaya", 18000),
    "B1": ("Agua mineral", 8000),
    "B2": ("Coca-Cola", 12000),
    "B3": ("Jugo natural", 15000),
}


class Producto:

    def __init__(self, codigo, nombre, precio, disponible=True):
        self.codigo = codigo
        self.nombre = nombre
        self.precio = precio
        self.disponible = disponible

    def mostrar_informacion(self):
        estado = "" if self.disponible else "  (AGOTADO)"
        print(f"  {self.codigo}  {self.nombre:<24} {self.precio:>7,} Gs.{estado}")


class Carta:

    def __init__(self):
        self.productos = {}
        self.cargar()

    def cargar(self):
        """Lee la carta de la base, o la crea con los productos iniciales la primera vez."""
        with conexion() as con:
            filas = con.execute(
                "SELECT codigo, nombre, precio, disponible FROM productos ORDER BY rowid").fetchall()
        if not filas:
            for codigo, (nombre, precio) in INICIALES.items():
                self.productos[codigo] = Producto(codigo, nombre, precio)
            self.guardar()
            return
        for fila in filas:
            self.productos[fila["codigo"]] = Producto(
                fila["codigo"], fila["nombre"], fila["precio"], bool(fila["disponible"]))

    def guardar(self):
        """Guarda la carta completa; si un producto ya existe, solo se actualiza."""
        with conexion() as con:
            con.executemany(
                """INSERT INTO productos (codigo, nombre, precio, disponible) VALUES (?, ?, ?, ?)
                   ON CONFLICT(codigo) DO UPDATE SET nombre = excluded.nombre,
                       precio = excluded.precio, disponible = excluded.disponible""",
                [(p.codigo, p.nombre, p.precio, int(p.disponible)) for p in self.productos.values()])

    def obtener(self, codigo):
        return self.productos.get(codigo.upper())

    def mostrar(self, solo_disponibles=False):
        print("\n--- CARTA DEL RESTAURANTE ---")
        for producto in self.productos.values():
            if solo_disponibles and not producto.disponible:
                continue
            producto.mostrar_informacion()

    def buscar(self, texto):
        """Busca por nombre recorriendo toda la carta con búsqueda lineal."""
        texto = texto.lower()
        return [p for p in self.productos.values() if texto in p.nombre.lower()]

    def ordenar_por_precio(self):
        """Ordena los productos de menor a mayor precio con el método burbuja."""
        lista = list(self.productos.values())
        for i in range(len(lista) - 1):
            for j in range(len(lista) - 1 - i):
                if lista[j].precio > lista[j + 1].precio:
                    lista[j], lista[j + 1] = lista[j + 1], lista[j]
        return lista

    def combo_optimo(self, presupuesto):
        """Arma el combo que mejor aprovecha el presupuesto con programación dinámica.

        Es el problema de la mochila: cada producto entra entero o no entra. La tabla
        guarda la solución de cada subproblema para no tener que recalcularla.
        """
        # Se trabaja en miles de guaraníes porque todos los precios son múltiplos de
        # mil, así la tabla tiene decenas de columnas y no decenas de miles
        ESCALA = 1000
        lista = [p for p in self.productos.values() if p.disponible]
        capacidad = presupuesto // ESCALA
        pesos = [p.precio // ESCALA for p in lista]
        if capacidad <= 0 or not lista:
            return [], 0

        # dp[i][w] es el mayor gasto posible con los primeros i productos y capacidad w
        dp = [[0] * (capacidad + 1) for _ in range(len(lista) + 1)]
        for i in range(1, len(lista) + 1):
            for w in range(capacidad + 1):
                if pesos[i - 1] <= w:
                    dp[i][w] = max(pesos[i - 1] + dp[i - 1][w - pesos[i - 1]], dp[i - 1][w])
                else:
                    dp[i][w] = dp[i - 1][w]

        # Recorriendo la tabla hacia atrás se sabe qué productos entraron: si el valor
        # cambió al sumar el producto i, es porque ese producto fue elegido
        elegidos, w = [], capacidad
        for i in range(len(lista), 0, -1):
            if dp[i][w] != dp[i - 1][w]:
                elegidos.append(lista[i - 1])
                w -= pesos[i - 1]
        elegidos.reverse()
        return elegidos, dp[len(lista)][capacidad] * ESCALA

    def cambiar_disponibilidad(self, codigo):
        producto = self.obtener(codigo)
        if producto:
            producto.disponible = not producto.disponible
            self.guardar()
        return producto


def obtener_carta(restaurante):
    """Devuelve la carta del restaurante, y la crea si el módulo se usa solo."""
    if restaurante is None:
        return Carta()
    if getattr(restaurante, "carta", None) is None:
        restaurante.carta = Carta()
    return restaurante.carta


# Orientacion que se muestra arriba del menu: que escribir en cada campo
AYUDA = [
    "MENU: consulte la carta, busque platos y vea precios.",
    "Codigos de platos: letra y numero, por ejemplo  P1  (plato) o  B2  (bebida)",
    "Presupuesto: guaranies sin puntos ni comas, por ejemplo  100000",
]


def menu(restaurante=None):
    carta = obtener_carta(restaurante)

    # 'esperar' vale True despues de ejecutar una opcion: antes de limpiar la
    # pantalla se espera un Enter para que el usuario alcance a leer el resultado.
    esperar = False

    while True:
        if esperar:
            pausa()
        limpiar()   # pantalla limpia en cada vuelta: la terminal no se llena de texto
        titulo("MODULO MENU")
        for linea in AYUDA:
            info(linea)
        print("1. Ver carta")
        print("2. Buscar producto")
        print("3. Ordenar por precio")
        print("4. Combo óptimo según presupuesto")
        print("5. Marcar producto agotado o disponible")
        print("0. Volver")
        opcion = pedir("Opcion", "escriba el numero y Enter, ej.: 1")
        esperar = True
        print()

        if opcion == "1":
            carta.mostrar()

        elif opcion == "2":
            texto = pedir("Buscar", "parte del nombre del plato, ej.: milanesa")
            if not texto:
                # Un texto vacio coincidiria con todos los productos: se avisa en vez de listar todo
                error("No escribió nada para buscar. Escriba parte del nombre\n"
                      "de un plato, por ejemplo: milanesa.")
                continue
            resultados = carta.buscar(texto)
            if not resultados:
                error("No hay ningún producto cuyo nombre contenga ese texto.")
            for producto in resultados:
                producto.mostrar_informacion()

        elif opcion == "3":
            for producto in carta.ordenar_por_precio():
                producto.mostrar_informacion()

        elif opcion == "4":
            # pedir_entero repite la pregunta si hay letras, decimales o un 0, y Enter vacio cancela
            presupuesto = pedir_entero("Presupuesto en Gs.", "100000", minimo=1)
            if presupuesto is None:
                continue
            elegidos, total = carta.combo_optimo(presupuesto)
            if not elegidos:
                error("Con ese presupuesto no alcanza ni para el producto más\n"
                      f"barato de la carta, que cuesta {min(p.precio for p in carta.productos.values()):,} Gs.")
                continue
            for producto in elegidos:
                producto.mostrar_informacion()
            ok(f"TOTAL: {total:,} Gs. (sobra {presupuesto - total:,} Gs.)")

        elif opcion == "5":
            carta.mostrar()
            producto = carta.cambiar_disponibilidad(
                pedir("Codigo", "uno de la lista de arriba, ej.: P1 o B2"))
            if producto is None:
                error("Ese código no está en la carta. Hay que escribir uno de los\n"
                      "que aparecen en la lista de arriba, por ejemplo P1 o B2.")
            else:
                ok(f"{producto.nombre}: "
                   f"{'disponible' if producto.disponible else 'AGOTADO'}")

        elif opcion == "0":
            break   # vuelve al menu principal sin esperar Enter

        else:
            # Cualquier otra cosa no es una opcion del menu
            error(f"'{opcion}' no es una opción del menú. Escriba uno de los\n"
                  "números de la lista, por ejemplo 1.")
