"""Interfaz web de RestauPy hecha con Streamlit.

Usa las mismas clases y la misma base de datos que la version de consola, asi que
las dos se pueden usar al mismo tiempo: lo que se carga en una aparece en la otra.

Se ejecuta con:  py -m streamlit run app.py
"""
import re
from datetime import datetime, timedelta
from types import SimpleNamespace

import altair as alt
import pandas as pd
import streamlit as st

from main import siguiente_paso
from modulos.base_datos import (cargar_mesas, clientes_de_hoy, guardar_mesas,
                                platos_vendidos_desde, registrar_cliente, ventas_desde)
from modulos.caja import IVA, calcular_cuenta, cerrar_cuenta
from modulos.menu import Carta
from modulos.mesa import MAX_CAPACIDAD, MAX_NUMERO_MESA, Mesa
from modulos.mozo import COBRADA, EN_PREPARACION, ENTREGADA, LISTA, PENDIENTE, Mozo
from modulos.pass_ import LIMITE_DEMORA, Pass

# Mismas reglas que pedir_texto en la consola: solo letras, espacios y - ' .
NOMBRE_VALIDO = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü' .-]+$")
ICONOS = {PENDIENTE: "🟡", EN_PREPARACION: "🟠", LISTA: "🟢", ENTREGADA: "🔵", COBRADA: "⚪"}

st.set_page_config(page_title="RestauPy", page_icon="🍽️", layout="wide")


def gs(valor):
    """Formatea un monto en guaranies con punto de miles, como se escribe aca."""
    return f"{round(valor):,} Gs.".replace(",", ".")


def avisar(tipo, texto):
    """Guarda un mensaje para mostrarlo despues de recargar la pagina."""
    st.session_state.aviso = (tipo, texto)
    st.rerun()


def mostrar_aviso():
    if "aviso" in st.session_state:
        tipo, texto = st.session_state.pop("aviso")
        {"ok": st.success, "error": st.error}.get(tipo, st.info)(texto)


def comanda_activa(mozo, numero_mesa):
    """Una mesa tiene comanda activa mientras no se haya entregado ni cobrado."""
    return any(c.mesa == numero_mesa and c.estado not in (ENTREGADA, COBRADA)
               for c in mozo.comandas)


def sin_cobrar(mozo, numero_mesa):
    return any(c.mesa == numero_mesa and c.estado != COBRADA for c in mozo.comandas)


def detalle(comanda, carta):
    """Texto corto con los platos de una comanda y sus observaciones."""
    partes = []
    for item in comanda.items:
        producto = carta.obtener(item["codigo"])
        nombre = producto.nombre if producto else item["codigo"]
        partes.append(f"{item['cantidad']} × {nombre}" + (f" ({item['obs']})" if item["obs"] else ""))
    return ", ".join(partes) or "Sin platos todavía"


# Streamlit vuelve a ejecutar este archivo en cada clic, asi que los datos se leen
# de la base en cada vuelta y siempre estan al dia
carta = Carta()
mesas = cargar_mesas()
registro = Mozo("Sistema")

st.sidebar.title("🍽️ RestauPy")
st.sidebar.caption("De la mesa a la caja")
pagina = st.sidebar.radio("Módulo", ["Inicio", "Clientes", "Mesas", "Menú", "Mozo",
                                     "Cocina", "Caja", "Reportes"])
mostrar_aviso()


if pagina == "Inicio":
    st.title("Resumen del restaurante")
    st.info("**Siguiente paso:** " + siguiente_paso(SimpleNamespace(mesas=mesas, carta=carta)))

    hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    libres = sum(1 for m in mesas.values() if m.estado == "Libre")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mesas libres", f"{libres} de {len(mesas)}")
    c2.metric("En cocina", len(registro.por_estado(EN_PREPARACION)))
    c3.metric("Listas para entregar", len(registro.por_estado(LISTA)))
    c4.metric("Ventas de hoy", gs(sum(v["total"] for v in ventas_desde(hoy))))

    izquierda, derecha = st.columns(2)
    with izquierda:
        st.subheader("Mesas")
        if not mesas:
            st.caption("Todavía no hay mesas registradas.")
        for mesa in mesas.values():
            color = "🟢" if mesa.estado == "Libre" else "🔴"
            st.write(f"{color} Mesa {mesa.numero} · {mesa.capacidad} personas · {mesa.estado}")
    with derecha:
        st.subheader("Comandas en curso")
        activas = [c for c in registro.comandas if c.estado not in (COBRADA,)]
        if not activas:
            st.caption("No hay comandas en curso.")
        for c in activas:
            st.write(f"{ICONOS[c.estado]} #{c.numero} · Mesa {c.mesa} · {c.estado}")


elif pagina == "Clientes":
    st.title("Clientes")
    libres = [m.numero for m in mesas.values() if m.estado == "Libre"]
    with st.form("cliente", clear_on_submit=True):
        nombre = st.text_input("Nombre y apellido", placeholder="ej.: Arturo Fleitas")
        mesa_elegida = st.selectbox("Mesa donde se sienta", ["Sin mesa todavía"] + libres,
                                    format_func=lambda m: m if isinstance(m, str) else f"Mesa {m}")
        if st.form_submit_button("Registrar cliente", type="primary"):
            nombre = nombre.strip()
            if not 3 <= len(nombre) <= 40 or not NOMBRE_VALIDO.match(nombre):
                avisar("error", "El nombre tiene que tener entre 3 y 40 letras, sin números.")
            numero = None if isinstance(mesa_elegida, str) else mesa_elegida
            if numero:
                mesas[numero].ocupar()
                guardar_mesas(mesas)
            registrar_cliente(nombre, numero)
            avisar("ok", f"{nombre} registrado" + (f" y sentado en la mesa {numero}." if numero else "."))

    st.subheader("Llegaron hoy")
    clientes = clientes_de_hoy()
    if clientes:
        clientes = [{**c, "llegada": c["llegada"][11:16]} for c in clientes]   # solo la hora
        st.dataframe(pd.DataFrame(clientes).rename(columns={
            "nombre": "Nombre", "mesa": "Mesa", "llegada": "Hora de llegada"}),
            hide_index=True, use_container_width=True)
    else:
        st.caption("Todavía no se registró ningún cliente hoy.")


elif pagina == "Mesas":
    st.title("Mesas")
    with st.expander("Registrar una mesa nueva", expanded=not mesas):
        with st.form("mesa_nueva", clear_on_submit=True):
            c1, c2 = st.columns(2)
            numero = c1.number_input("Número de mesa", 1, MAX_NUMERO_MESA, 1)
            capacidad = c2.number_input("Capacidad (personas)", 1, MAX_CAPACIDAD, 4)
            if st.form_submit_button("Registrar", type="primary"):
                if numero in mesas:
                    avisar("error", f"La mesa {numero} ya está registrada.")
                mesas[numero] = Mesa(numero, capacidad)
                guardar_mesas(mesas)
                avisar("ok", f"Mesa {numero} registrada (capacidad {capacidad}).")

    if not mesas:
        st.caption("Todavía no hay mesas. Registre la primera arriba.")
    columnas = st.columns(4)
    for i, mesa in enumerate(mesas.values()):
        with columnas[i % 4].container(border=True):
            libre = mesa.estado == "Libre"
            st.markdown(f"### Mesa {mesa.numero}")
            st.caption(f"{mesa.capacidad} personas")
            st.markdown(("🟢 **Libre**" if libre else "🔴 **Ocupada**"))
            if libre and st.button("Ocupar", key=f"ocupar_{mesa.numero}", use_container_width=True):
                mesa.ocupar()
                guardar_mesas(mesas)
                avisar("ok", f"Mesa {mesa.numero} ocupada.")
            if not libre and st.button("Liberar", key=f"liberar_{mesa.numero}", use_container_width=True):
                # No se libera una mesa que todavia debe algo: primero se cobra en Caja
                if sin_cobrar(registro, mesa.numero):
                    avisar("error", f"La mesa {mesa.numero} tiene una comanda sin cobrar."
                                    " Primero cóbrela en Caja.")
                mesa.liberar()
                guardar_mesas(mesas)
                avisar("ok", f"Mesa {mesa.numero} liberada.")


elif pagina == "Menú":
    st.title("Menú")
    tab_carta, tab_combo, tab_disponibles = st.tabs(["Carta", "Combo óptimo", "Disponibilidad"])

    with tab_carta:
        c1, c2 = st.columns([3, 1])
        texto = c1.text_input("Buscar plato", placeholder="ej.: milanesa")
        ordenar = c2.toggle("Ordenar por precio")
        # Se usan los mismos metodos de la consola: busqueda lineal y burbuja
        productos = carta.buscar(texto) if texto else list(carta.productos.values())
        if ordenar:
            productos = [p for p in carta.ordenar_por_precio() if p in productos]
        st.dataframe(pd.DataFrame([{
            "Código": p.codigo, "Plato": p.nombre, "Precio": gs(p.precio),
            "Estado": "✅ Disponible" if p.disponible else "⛔ Agotado"} for p in productos]),
            hide_index=True, use_container_width=True)

    with tab_combo:
        st.write("El cliente dice cuánto quiere gastar y el sistema arma el combo que mejor "
                 "aprovecha ese monto, con programación dinámica.")
        presupuesto = st.number_input("Presupuesto en Gs.", min_value=1000, step=5000, value=100000)
        if st.button("Armar combo", type="primary"):
            elegidos, total = carta.combo_optimo(int(presupuesto))
            if not elegidos:
                st.warning("Con ese presupuesto no alcanza ni para el producto más barato.")
            else:
                c1, c2, c3 = st.columns(3)
                c1.metric("Presupuesto", gs(presupuesto))
                c2.metric("Total del combo", gs(total))
                c3.metric("Sobra", gs(presupuesto - total))
                st.dataframe(pd.DataFrame([{"Plato": p.nombre, "Precio": gs(p.precio)}
                                           for p in elegidos]),
                             hide_index=True, use_container_width=True)

    with tab_disponibles:
        st.caption("Destilde un plato cuando se agote: el mozo ya no lo va a poder pedir.")
        tabla = pd.DataFrame([{"Código": p.codigo, "Plato": p.nombre, "Disponible": p.disponible}
                              for p in carta.productos.values()])
        editada = st.data_editor(tabla, disabled=["Código", "Plato"], hide_index=True,
                                 use_container_width=True, key="disponibles")
        if not editada.equals(tabla):
            for fila in editada.itertuples():
                carta.productos[fila.Código].disponible = bool(fila.Disponible)
            carta.guardar()
            avisar("ok", "Disponibilidad actualizada.")


elif pagina == "Mozo":
    st.title("Mozo")
    nombre_mozo = st.text_input("Nombre del mozo", key="nombre_mozo", placeholder="ej.: Lucas")
    mozo = Mozo(nombre_mozo.strip() or "Sin nombre")
    disponibles = [p for p in carta.productos.values() if p.disponible]

    st.subheader("Abrir comanda")
    para_atender = [m.numero for m in mesas.values()
                    if m.estado == "Ocupada" and not comanda_activa(mozo, m.numero)]
    if not para_atender:
        st.caption("No hay mesas ocupadas esperando pedido. Ocupe una en Mesas o Clientes.")
    else:
        c1, c2 = st.columns([3, 1])
        mesa_elegida = c1.selectbox("Mesa", para_atender, format_func=lambda m: f"Mesa {m}")
        c2.write("")
        if c2.button("Abrir comanda", type="primary", use_container_width=True):
            if not nombre_mozo.strip() or not NOMBRE_VALIDO.match(nombre_mozo.strip()):
                avisar("error", "Escriba el nombre del mozo (solo letras) antes de abrir la comanda.")
            comanda = mozo.nueva_comanda(mesa_elegida)
            avisar("ok", f"Comanda #{comanda.numero} abierta para la mesa {mesa_elegida}."
                         " Cargue los platos abajo.")

    st.subheader("Comandas por cargar")
    pendientes = mozo.por_estado(PENDIENTE)
    if not pendientes:
        st.caption("No hay comandas abiertas.")
    for comanda in pendientes:
        with st.container(border=True):
            st.markdown(f"**Comanda #{comanda.numero} · Mesa {comanda.mesa}** · "
                        f"{gs(comanda.calcular_total(carta))}")
            st.caption(detalle(comanda, carta))
            c1, c2, c3, c4 = st.columns([3, 1, 2, 1.2])
            codigo = c1.selectbox("Plato", [p.codigo for p in disponibles], key=f"plato_{comanda.numero}",
                                  format_func=lambda c: f"{c} · {carta.obtener(c).nombre}")
            cantidad = c2.number_input("Cantidad", 1, 20, 1, key=f"cant_{comanda.numero}")
            obs = c3.text_input("Observación", key=f"obs_{comanda.numero}", placeholder="ej.: sin cebolla")
            c4.write("")
            if c4.button("Agregar", key=f"agregar_{comanda.numero}", use_container_width=True):
                comanda.agregar_item(codigo, int(cantidad), obs.strip())
                mozo.guardar(comanda)
                avisar("ok", f"{cantidad} × {carta.obtener(codigo).nombre} agregado a la comanda #{comanda.numero}.")
            if st.button("Enviar a cocina", key=f"enviar_{comanda.numero}", type="primary",
                         disabled=not comanda.items):
                mozo.cambiar_estado(comanda, EN_PREPARACION)
                avisar("ok", f"Comanda #{comanda.numero} enviada a la cocina.")

    st.subheader("Listas para entregar")
    listas = mozo.por_estado(LISTA)
    if not listas:
        st.caption("La cocina todavía no terminó ninguna comanda.")
    for comanda in listas:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"🟢 **Comanda #{comanda.numero} · Mesa {comanda.mesa}**  \n{detalle(comanda, carta)}")
            if c2.button("Entregar", key=f"entregar_{comanda.numero}", use_container_width=True):
                mozo.cambiar_estado(comanda, ENTREGADA)
                avisar("ok", f"Comanda #{comanda.numero} entregada en la mesa {comanda.mesa}.")


elif pagina == "Cocina":
    st.title("Cocina")
    st.caption(f"Orden de salida: la comanda más antigua primero. Desde {LIMITE_DEMORA} minutos"
               " de espera se marca como demorada.")
    cocina = Pass(carta)
    if not cocina.cola:
        st.info("No hay comandas en cocina. Llegan cuando el mozo usa «Enviar a cocina».")
    for posicion, comanda in enumerate(cocina.cola):
        espera = comanda.minutos_de_espera()
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            encabezado = f"**Comanda #{comanda.numero} · Mesa {comanda.mesa} · Mozo {comanda.mozo}**"
            if posicion == 0:
                encabezado = "⭐ Siguiente en salir · " + encabezado
            c1.markdown(encabezado)
            if espera >= LIMITE_DEMORA:
                c1.error(f"DEMORADA: {espera} min de espera")
            else:
                c1.caption(f"Espera: {espera} min")
            for item in comanda.items:
                producto = carta.obtener(item["codigo"])
                c1.write(f"{item['cantidad']} × {producto.nombre if producto else item['codigo']}"
                         + (f" — _{item['obs']}_" if item["obs"] else ""))
            if c2.button("Marcar lista", key=f"lista_{comanda.numero}", type="primary",
                         use_container_width=True):
                cocina.marcar_lista(comanda)
                avisar("ok", f"Comanda #{comanda.numero} lista. Avisar al mozo {comanda.mozo}.")


elif pagina == "Caja":
    st.title("Caja")
    entregadas = registro.por_estado(ENTREGADA)
    if not entregadas:
        st.info("No hay mesas con cuenta para cobrar. Aparecen cuando el mozo entrega la comanda.")
    else:
        con_deuda = sorted({c.mesa for c in entregadas})
        numero = st.selectbox("Mesa a cobrar", con_deuda, format_func=lambda m: f"Mesa {m}")
        comandas_mesa = [c for c in entregadas if c.mesa == numero]
        filas = []
        for c in comandas_mesa:
            for item in c.items:
                producto = carta.obtener(item["codigo"])
                precio = producto.precio if producto else 0
                filas.append({"Comanda": f"#{c.numero}", "Plato": producto.nombre if producto else item["codigo"],
                              "Cantidad": item["cantidad"], "Precio": gs(precio),
                              "Importe": gs(precio * item["cantidad"])})
        st.dataframe(pd.DataFrame(filas), hide_index=True, use_container_width=True)

        subtotal, impuesto, total = calcular_cuenta(comandas_mesa, carta)
        c1, c2, c3 = st.columns(3)
        c1.metric("Subtotal", gs(subtotal))
        c2.metric(f"IVA ({IVA:.0%})", gs(impuesto))
        c3.metric("Total a pagar", gs(total))
        if st.button("Confirmar cobro", type="primary"):
            cerrar_cuenta(numero, comandas_mesa, registro, mesas, carta)
            guardar_mesas(mesas)
            avisar("ok", f"Mesa {numero} cobrada ({gs(total)}) y liberada.")

    st.subheader("Ventas de hoy")
    hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    ventas = ventas_desde(hoy)
    if ventas:
        tabla = pd.DataFrame(ventas)
        tabla["fecha"] = tabla["fecha"].str[11:16]
        for columna in ("subtotal", "iva", "total"):
            tabla[columna] = tabla[columna].map(gs)
        st.dataframe(tabla.rename(columns={"fecha": "Hora", "mesa": "Mesa", "comandas": "Comandas",
                                           "subtotal": "Subtotal", "iva": "IVA", "total": "Total"}),
                     hide_index=True, use_container_width=True)
        st.metric("Total del día", gs(sum(v["total"] for v in ventas)))
    else:
        st.caption("Todavía no hubo cobros hoy.")


elif pagina == "Reportes":
    st.title("Platos más vendidos")
    periodo = st.radio("Período", ["Hoy", "Últimos 7 días"], horizontal=True)
    ahora = datetime.now()
    desde = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    if periodo == "Últimos 7 días":
        desde -= timedelta(days=6)
    vendidos = pd.DataFrame(platos_vendidos_desde(desde))
    if vendidos.empty:
        st.info("No hay comandas entregadas o cobradas en ese período.")
    else:
        mas_vendido = vendidos.iloc[0]
        st.metric("El más pedido", mas_vendido["plato"])
        st.caption(f"{mas_vendido['cantidad']} unidades vendidas")
        grafico = alt.Chart(vendidos).mark_bar(color="#C8553D").encode(
            x=alt.X("cantidad:Q", title="Unidades vendidas"),
            y=alt.Y("plato:N", sort="-x", title=None,
                    axis=alt.Axis(labelLimit=220, labelFontSize=14)),
            tooltip=["plato", "cantidad"])
        etiquetas = grafico.mark_text(align="left", dx=4, fontSize=13).encode(text="cantidad:Q")
        st.altair_chart((grafico + etiquetas).properties(height=36 * len(vendidos) + 40),
                        use_container_width=True)
