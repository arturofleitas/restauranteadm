
"""Modulo para gestionar las mesas del restaurante."""


class Mesa:

    # Constructor: guarda los datos de cada mesa.
    def __init__(self, numero, capacidad):
        self.numero = numero
        self.capacidad = capacidad
        self.estado = "Libre"

    # Cambia el estado de la mesa a ocupada.
    def ocupar(self):
        if self.estado == "Libre":
            self.estado = "Ocupada"
            return True
        return False

    # Cambia el estado de la mesa a libre.
    def liberar(self):
        if self.estado == "Ocupada":
            self.estado = "Libre"
            return True
        return False

    # Muestra la informacion de la mesa.
    def mostrar(self):
        print(f"Mesa {self.numero} | Capacidad: {self.capacidad} | Estado: {self.estado}")


# Menu principal del modulo Mesa.
def menu():
    mesas = {}

    while True:
        print("\n===== GESTION DE MESAS =====")
        print("1. Registrar mesa")
        print("2. Consultar mesas")
        print("3. Ocupar mesa")
        print("4. Liberar mesa")
        print("5. Consultar mesas disponibles")
        print("0. Salir")

        opcion = input("Seleccione una opcion: ").strip()

        if opcion == "1":
            try:
                numero = int(input("Numero de mesa: "))
                capacidad = int(input("Capacidad de personas: "))

                if numero <= 0 or capacidad <= 0:
                    print("Ingrese valores mayores que cero.")
                elif numero in mesas:
                    print("Esta mesa ya esta registrada.")
                else:
                    mesas[numero] = Mesa(numero, capacidad)
                    print("Mesa registrada correctamente.")

            except ValueError:
                print("Ingrese numeros validos.")

        elif opcion == "2":
            if not mesas:
                print("No hay mesas registradas.")
            else:
                for mesa in mesas.values():
                    mesa.mostrar()

        elif opcion == "3":
            try:
                numero = int(input("Numero de mesa: "))
                mesa = mesas.get(numero)

                if mesa is None:
                    print("Mesa no encontrada.")
                elif mesa.ocupar():
                    print("Mesa ocupada correctamente.")
                else:
                    print("La mesa ya esta ocupada.")

            except ValueError:
                print("Ingrese un numero valido.")

        elif opcion == "4":
            try:
                numero = int(input("Numero de mesa: "))
                mesa = mesas.get(numero)

                if mesa is None:
                    print("Mesa no encontrada.")
                elif mesa.liberar():
                    print("Mesa liberada correctamente.")
                else:
                    print("La mesa ya esta libre.")

            except ValueError:
                print("Ingrese un numero valido.")

        elif opcion == "5":
            disponibles = 0

            for mesa in mesas.values():
                if mesa.estado == "Libre":
                    mesa.mostrar()
                    disponibles += 1

            if disponibles == 0:
                print("No hay mesas disponibles.")

        elif opcion == "0":
            print("Saliendo de gestion de mesas...")
            break

        else:
            print("Opcion invalida.")


# Ejecuta el menu al iniciar este archivo.
if __name__ == "__main__":
    menu()
