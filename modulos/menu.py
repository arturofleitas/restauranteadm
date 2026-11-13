import json
import os

ARCHIVO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos", "menu.json")

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
        """Lee la carta del JSON, o la crea con los productos iniciales la primera vez."""
        if not os.path.exists(ARCHIVO):
            for codigo, (nombre, precio) in INICIALES.items():
                self.productos[codigo] = Producto(codigo, nombre, precio)
            self.guardar()
            return
        with open(ARCHIVO, encoding="utf-8") as archivo:
            for codigo, datos in json.load(archivo).items():
                self.productos[codigo] = Producto(
                    codigo, datos["nombre"], datos["precio"], datos["disponible"])

    def guardar(self):
        """Escribe la carta completa en el JSON."""
        os.makedirs(os.path.dirname(ARCHIVO), exist_ok=True)
        datos = {p.codigo: {"nombre": p.nombre, "precio": p.precio,
                            "disponible": p.disponible} for p in self.productos.values()}
        with open(ARCHIVO, "w", encoding="utf-8") as archivo:
            # ensure_ascii en falso conserva las tildes legibles dentro del archivo
            json.dump(datos, archivo, indent=2, ensure_ascii=False)

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


def menu(restaurante=None):
    carta = obtener_carta(restaurante)

    while True:
        print("\n=== MODULO MENU ===")
        print("1. Ver carta")
        print("2. Buscar producto")
        print("3. Ordenar por precio")
        print("4. Combo óptimo según presupuesto")
        print("5. Marcar producto agotado o disponible")
        print("0. Volver")
        opcion = input("Opción: ").strip()

        if opcion == "1":
            carta.mostrar()

        elif opcion == "2":
            resultados = carta.buscar(input("Buscar: ").strip())
            if not resultados:
                print("No se encontró ningún producto.")
            for producto in resultados:
                producto.mostrar_informacion()

        elif opcion == "3":
            for producto in carta.ordenar_por_precio():
                producto.mostrar_informacion()

        elif opcion == "4":
            texto = input("Presupuesto en Gs.: ").strip()
            if not texto.isdigit():
                print("Presupuesto inválido.")
                continue
            elegidos, total = carta.combo_optimo(int(texto))
            if not elegidos:
                print("No alcanza para ningún producto.")
                continue
            for producto in elegidos:
                producto.mostrar_informacion()
            print(f"  TOTAL: {total:,} Gs. (sobra {int(texto) - total:,} Gs.)")

        elif opcion == "5":
            carta.mostrar()
            producto = carta.cambiar_disponibilidad(input("Código: ").strip())
            if producto is None:
                print("Ese código no existe.")
            else:
                print(f"{producto.nombre}: "
                      f"{'disponible' if producto.disponible else 'AGOTADO'}")

        elif opcion == "0":
            break
