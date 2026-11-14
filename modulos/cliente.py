
"""Modulo para gestionar los clientes del restaurante."""


class Cliente:

    def __init__(self, codigo, nombre, cantidad_personas):
        self.codigo = codigo
        self.nombre = nombre
        self.cantidad_personas = cantidad_personas
        self.mesa = None

    def sentarse(self, mesa):
        if self.mesa is not None:
            return False

        if mesa.estado != "Libre":
            return False

        if self.cantidad_personas > mesa.capacidad:
            return False

        if mesa.ocupar():
            self.mesa = mesa
            return True

        return False

    def levantarse(self):
        if self.mesa is None:
            return False

        self.mesa.liberar()
        self.mesa = None
        return True

    def mostrar_informacion(self):
        print("\n--- INFORMACION DEL CLIENTE ---")
        print(f"Codigo: {self.codigo}")
        print(f"Nombre: {self.nombre}")
        print(f"Cantidad de personas: {self.cantidad_personas}")

        if self.mesa is not None:
            print(f"Mesa: {self.mesa.numero}")
            print("Estado: En atencion")
        else:
            print("Mesa: Sin asignar")


def registrar_cliente(restaurante):

    nombre = input("Nombre del cliente: ").strip()

    if not nombre:
        print("El nombre no puede estar vacio.")
        return

    try:
        cantidad = int(input("Cantidad de personas: "))

        if cantidad <= 0:
            print("La cantidad debe ser mayor que cero.")
            return

    except ValueError:
        print("Ingrese una cantidad valida.")
        return

    # Generar codigo unico.
    codigo = max(restaurante.clientes.keys(), default=0) + 1

    cliente = Cliente(codigo, nombre, cantidad)

    restaurante.clientes[codigo] = cliente

    print("\nCliente registrado correctamente.")
    cliente.mostrar_informacion()


def listar_clientes(restaurante):

    if not restaurante.clientes:
        print("\nNo hay clientes registrados.")
        return

    print("\n===== LISTA DE CLIENTES =====")

    for cliente in restaurante.clientes.values():
        cliente.mostrar_informacion()


def buscar_cliente(restaurante):

    try:
        codigo = int(input("Ingrese el codigo del cliente: "))
    except ValueError:
        print("Ingrese un codigo valido.")
        return

    cliente = restaurante.clientes.get(codigo)

    if cliente is None:
        print("Cliente no encontrado.")
    else:
        cliente.mostrar_informacion()


def asignar_mesa(restaurante):

    try:
        codigo = int(input("Codigo del cliente: "))
    except ValueError:
        print("Codigo invalido.")
        return

    cliente = restaurante.clientes.get(codigo)

    if cliente is None:
        print("Cliente no encontrado.")
        return

    if cliente.mesa is not None:
        print("El cliente ya tiene una mesa asignada.")
        return

    disponibles = [
        mesa for mesa in restaurante.mesas.values()
        if mesa.estado == "Libre"
        and mesa.capacidad >= cliente.cantidad_personas
    ]

    if not disponibles:
        print("No hay mesas disponibles con capacidad suficiente.")
        return

    print("\n===== MESAS DISPONIBLES =====")

    for mesa in disponibles:
        mesa.mostrar()

    try:
        numero = int(input("Seleccione el numero de mesa: "))
    except ValueError:
        print("Ingrese un numero valido.")
        return

    mesa = restaurante.mesas.get(numero)

    if mesa is None:
        print("La mesa no existe.")
        return

    if cliente.sentarse(mesa):
        print("Mesa asignada correctamente.")
        cliente.mostrar_informacion()
    else:
        print("No fue posible asignar esta mesa.")


def liberar_mesa(restaurante):

    try:
        codigo = int(input("Codigo del cliente: "))
    except ValueError:
        print("Codigo invalido.")
        return

    cliente = restaurante.clientes.get(codigo)

    if cliente is None:
        print("Cliente no encontrado.")
        return

    if cliente.levantarse():
        print("La mesa fue liberada correctamente.")
    else:
        print("Este cliente no tiene una mesa asignada.")


def menu(restaurante):

    while True:
        print("\n===== MODULO CLIENTE =====")
        print("1. Registrar cliente")
        print("2. Listar clientes")
        print("3. Buscar cliente")
        print("4. Asignar mesa")
        print("5. Liberar mesa")
        print("0. Volver al menu principal")

        opcion = input("Seleccione una opcion: ").strip()

        if opcion == "1":
            registrar_cliente(restaurante)

        elif opcion == "2":
            listar_clientes(restaurante)

        elif opcion == "3":
            buscar_cliente(restaurante)

        elif opcion == "4":
            asignar_mesa(restaurante)

        elif opcion == "5":
            liberar_mesa(restaurante)

        elif opcion == "0":
            break

        else:
            print("Opcion invalida.")
