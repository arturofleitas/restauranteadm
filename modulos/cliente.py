from modulos.base_datos import registrar_cliente
from modulos.entrada import ok, pedir_texto


# Representa a una persona que llega al restaurante.
class Cliente:

    # Constructor: guarda el nombre y deja la mesa sin asignar.
    def __init__(self, nombre):
        self.nombre = nombre
        self.mesa = None

    # Asocia el cliente a una mesa.
    def sentarse(self, mesa):
        self.mesa = mesa

    # Muestra los datos del cliente en pantalla.
    def mostrar_informacion(self):
        print("\n--- INFORMACION DEL CLIENTE ---")
        print(f"Nombre: {self.nombre}")

        if self.mesa is not None:
            print(f"Mesa: {self.mesa.numero}")
        else:
            print("Mesa: Sin asignar")


# Pide el nombre del cliente validandolo y lo registra.
# Devuelve el Cliente creado, o None si el usuario cancela con Enter vacio.
def menu(restaurante):
    print("\n=== MODULO CLIENTE ===")

    # pedir_texto valida: solo letras y espacios, de 3 a 40 caracteres.
    # Si hay un error muestra un mensaje en rojo con un ejemplo y vuelve a preguntar.
    nombre = pedir_texto("Nombre del cliente", "Arturo Fleitas", minimo=3,
                         maximo=40, solo_letras=True)
    if nombre is None:      # el usuario cancelo con Enter
        return

    cliente = Cliente(nombre)
    registrar_cliente(nombre)   # queda guardado con la fecha y hora de llegada

    print()
    ok("Cliente registrado correctamente.")
    cliente.mostrar_informacion()

    return cliente
