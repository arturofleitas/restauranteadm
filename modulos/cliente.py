
class Cliente:

    def __init__(self, nombre):
        self.nombre = nombre
        self.mesa = None

    def sentarse(self, mesa):
        self.mesa = mesa

    def mostrar_informacion(self):
        print("\n--- INFORMACION DEL CLIENTE ---")
        print(f"Nombre: {self.nombre}")

        if self.mesa is not None:
            print(f"Mesa: {self.mesa.numero}")
        else:
            print("Mesa: Sin asignar")


def menu(restaurante):
    print("\n=== MODULO CLIENTE ===")

    nombre = input("Ingrese el nombre del cliente: ").strip()

    if not nombre:
        print("El nombre no puede estar vacío.")
        return

    cliente = Cliente(nombre)

    print("\nCliente registrado correctamente.")
    cliente.mostrar_informacion()

    return cliente
