"""
Interfaz visual de RestauPy.

Diseño de la portada del restaurante con Rich y Pyfiglet.
Este archivo no modifica los módulos del equipo.
"""

from itertools import zip_longest

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich import box
from pyfiglet import figlet_format


console = Console()


# --------------------------------------------------
# DIBUJO DEL MOZO
# --------------------------------------------------

CHEF = r"""
       ___       ___
    .-'   '-._.-'   '-.
   /   .-.   |   .-.   \
  (   (   )  |  (   )   )
   '._ '.___.' '.__.' _.'
      '-._________.-'
      .-'  _____  '-.
     /   /       \   \
    |   |  ^   ^  |   |       ( (
    |   |  o   o  |   |      ) )
    |   |   \_/   |   |   .-~~~~~-.
     \   \  ___  /   /___/         \
      '-._'-----'_.-'   \___________/
       /  '-----'  \    '---------'
   ___/  /|  o  |\  \___    | |
  /  _  / |  o  | \  _  \   | |
 |  ( )|  |  o  |  |( )  |   |_|
  \____/   |____|   \____/
           /_/  \_\
""".strip("\n")


# --------------------------------------------------
# DIBUJO DE LA PIZZA
# --------------------------------------------------

PIZZA = r"""
       /\
      / o\
     / ●  \
    / o ● \
   / ●  o \
  / o  ●  o\
 /__________\
 \__________/
""".strip("\n")


# --------------------------------------------------
# CAMPANA DEL PANEL DE BIENVENIDA
# --------------------------------------------------

CAMPANA = r"""
     (  )
      )(
    .----.
  .'      '.
 /__________\
 '----------'
""".strip("\n")


# --------------------------------------------------
# COLORES DEL MOZO
# --------------------------------------------------

def chef_coloreado():
    """
    Aplica colores al rostro y al vapor del mozo.
    Mantiene el gorro y el uniforme en blanco.
    """

    dibujo = Text(
        CHEF,
        style="bold bright_white",
        no_wrap=True
    )

    inicio = 0

    for fila in CHEF.splitlines():

        detalles = [
            ("^   ^", "bright_green"),
            ("o   o", "bright_magenta"),
            ("( (", "bright_cyan"),
            (") )", "bright_cyan")
        ]

        for detalle, color in detalles:

            posicion = fila.find(detalle)

            if posicion >= 0:
                dibujo.stylize(
                    color,
                    inicio + posicion,
                    inicio + posicion + len(detalle)
                )

        inicio += len(fila) + 1

    return dibujo


# --------------------------------------------------
# TÍTULO RESTAU PY COMPLETAMENTE AZUL
# --------------------------------------------------

def titulo_azul(espacio):
    """
    Genera el título Restau Py en azul celeste.

    Las dos partes usan la misma tipografía y se
    alinean por filas para evitar superposiciones.
    """

    fuentes = [
        "slant",
        "standard",
        "small"
    ]

    for fuente in fuentes:

        # Generar la primera parte del nombre.
        restau = figlet_format(
            "Restau",
            font=fuente
        ).rstrip("\n").splitlines()

        # Generar la segunda parte del nombre.
        py = figlet_format(
            "Py",
            font=fuente
        ).rstrip("\n").splitlines()

        ancho_restau = max(
            len(linea) for linea in restau
        )

        ancho_py = max(
            len(linea) for linea in py
        )

        separacion = 2

        ancho_total = (
            ancho_restau
            + separacion
            + ancho_py
        )

        # Usar únicamente fuentes que entren en el cuadro.
        if ancho_total <= espacio:

            titulo = Text(no_wrap=True)

            cantidad_filas = max(
                len(restau),
                len(py)
            )

            for indice, (izquierda, derecha) in enumerate(
                zip_longest(
                    restau,
                    py,
                    fillvalue=""
                )
            ):

                # RESTAU en azul.
                titulo.append(
                    izquierda.ljust(ancho_restau),
                    style="bold bright_cyan"
                )

                # Separación visual.
                titulo.append("  ")

                # PY también en azul.
                titulo.append(
                    derecha,
                    style="bold bright_cyan"
                )

                if indice < cantidad_filas - 1:
                    titulo.append("\n")

            return titulo

    # Versión alternativa para terminales pequeñas.
    titulo = Text()

    titulo.append(
        "Restau",
        style="bold bright_cyan"
    )

    titulo.append(
        "  Py",
        style="bold bright_cyan"
    )

    return titulo


# --------------------------------------------------
# PANTALLA PRINCIPAL
# --------------------------------------------------

def mostrar_inicio(mesas=None, opciones_menu=None):
    """Muestra la portada principal de RestauPy.

    main.py pasa las mesas compartidas y la lista de opciones del menu,
    para que la portada dibuje siempre las mismas opciones que el programa.
    """

    if mesas is None:
        mesas = {}

    ocupadas = sum(
        1
        for mesa in mesas.values()
        if mesa.estado == "Ocupada"
    )

    ancho = console.size.width

    console.clear()

    # ----------------------------------------------
    # CABECERA: MOZO + RESTAU PY + PIZZA
    # ----------------------------------------------

    if ancho >= 130:

        ancho_chef = 38
        ancho_titulo = 65
        ancho_pizza = 16

        cabecera = Table.grid(
            expand=False,
            padding=(0, 1)
        )

        cabecera.add_column(
            width=ancho_chef,
            no_wrap=True
        )

        cabecera.add_column(
            width=ancho_titulo,
            no_wrap=True
        )

        cabecera.add_column(
            width=ancho_pizza,
            no_wrap=True
        )

        # Título completo en azul.
        letras = titulo_azul(
            ancho_titulo - 4
        )

        marca = Panel(
            Align.center(
                letras,
                vertical="middle"
            ),
            width=ancho_titulo,
            height=13,
            border_style="bright_cyan",
            box=box.DOUBLE,
            padding=(0, 1),
            subtitle="Tu restaurante, en control",
            subtitle_align="center"
        )

        cabecera.add_row(
            chef_coloreado(),
            marca,
            Text(
                PIZZA,
                style="bold bright_yellow",
                no_wrap=True
            )
        )

        console.print(cabecera)

    else:

        # Adaptación para terminales pequeñas.
        console.print(
            Panel(
                Align.center(
                    titulo_azul(
                        max(15, ancho - 8)
                    )
                ),
                border_style="bright_cyan",
                box=box.DOUBLE,
                subtitle="Tu restaurante, en control"
            )
        )

        console.print(
            "[dim]Ampliá la terminal a 130 columnas "
            "para ver el mozo y la pizza.[/dim]"
        )

    # ----------------------------------------------
    # ESTADÍSTICAS
    # ----------------------------------------------

    console.print(
        f"[bold cyan]🍽 Mesas: "
        f"{ocupadas}/{len(mesas)}[/bold cyan]"
        "    [bold green]▂▄▆ Ventas del día: "
        "G. 0[/bold green]"
        "    [bold yellow]⚠ Alertas: 0[/bold yellow]"
    )

    console.rule(style="bright_cyan")

    # ----------------------------------------------
    # MENÚ PRINCIPAL
    # ----------------------------------------------

    opciones = Text()

    opciones.append(
        "=== MENÚ PRINCIPAL ===\n\n",
        style="bold bright_cyan"
    )

    # Si main.py no envia opciones, se usan estas por defecto.
    lista_opciones = opciones_menu or [
        ("1", "Cliente"),
        ("2", "Gestión de Mesas"),
        ("3", "Menú (Carta)"),
        ("4", "Mozo (Comandas)"),
        ("5", "Pass (Cocina)"),
        ("6", "Caja"),
        ("0", "Salir")
    ]

    for numero, nombre in lista_opciones:

        opciones.append(
            f"{numero}.  ",
            style="bold bright_yellow"
        )

        opciones.append(
            nombre + "\n",
            style="bright_white"
        )

    # ----------------------------------------------
    # PANEL DE BIENVENIDA
    # ----------------------------------------------

    bienvenida = Text(justify="center")

    bienvenida.append(
        "★ ¡Bienvenido!\n\n",
        style="bold bright_magenta"
    )

    bienvenida.append(
        "Disfrutá de una experiencia\n"
        "única en "
    )

    bienvenida.append(
        "RestauPy\n\n",
        style="bold bright_cyan"
    )

    bienvenida.append(
        CAMPANA + "\n",
        style="bold bright_white"
    )

    bienvenida.append(
        '"Buena comida, mejores momentos"',
        style="italic bright_green"
    )

    # ----------------------------------------------
    # PANELES COMPACTOS
    # ----------------------------------------------

    if ancho >= 88:

        paneles = Table.grid(
            expand=False,
            padding=(0, 1)
        )

        paneles.add_column(width=39)
        paneles.add_column(width=43)

        paneles.add_row(

            # Panel del menú principal.
            Panel(
                opciones,
                width=39,
                height=17,
                padding=(0, 3),
                border_style="bright_cyan",
                box=box.ROUNDED
            ),

            # Panel de bienvenida.
            Panel(
                Align.center(
                    bienvenida,
                    vertical="middle"
                ),
                width=43,
                height=17,
                border_style="bright_yellow",
                box=box.ROUNDED
            )
        )

        console.print(paneles)

    else:

        console.print(
            Panel(
                opciones,
                padding=(0, 3),
                border_style="bright_cyan"
            )
        )

        console.print(
            Panel(
                bienvenida,
                border_style="bright_yellow"
            )
        )

    # ----------------------------------------------
    # MENSAJE INFERIOR
    # ----------------------------------------------

    console.print(
        "\n[bold bright_green]"
        "➜ Seleccione una opción:"
        "[/bold bright_green]"
    )


# --------------------------------------------------
# INICIO DEL PROGRAMA
# --------------------------------------------------

if __name__ == "__main__":
    mostrar_inicio()