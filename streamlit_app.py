import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.colors import qualitative
from matplotlib.colors import to_hex, to_rgb

# Configuración inicial
st.set_page_config(layout="wide")
st.title("📊 Mapa de Calor de Aulas - UDLA")
st.markdown(
    "Selecciona un aula para visualizar su ocupación horaria y materias asignadas."
)


# Funciones auxiliares
def corregir_hora(h):
    h = str(h).zfill(4)
    return h[:2] + ":" + h[2:]


def aplicar_tonalidad(hex_color, ocup):
    """
    Mezcla el color base con blanco usando una curva cuadrática para aumentar contraste visual.
    """
    if not hex_color.startswith("#") or len(hex_color) != 7:
        return hex_color

    hex_color = hex_color.lstrip("#")
    try:
        r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        # aplicar curva cuadrática: ocup_mod crece más rápido
        ocup_mod = ocup**2
        r_blend = int((1 - ocup_mod) * 255 + ocup_mod * r)
        g_blend = int((1 - ocup_mod) * 255 + ocup_mod * g)
        b_blend = int((1 - ocup_mod) * 255 + ocup_mod * b)
        return f"rgb({r_blend},{g_blend},{b_blend})"
    except Exception as e:
        print("ERROR en aplicar_tonalidad:", e)
        return "rgb(204,204,204)"


# Cargar datos
archivoLaboratorios = "db/Laboratorios.xlsx"
archivoPA = "db/pregrado/Pregrado PA 2025.xlsx"
materias_df = pd.read_excel(archivoLaboratorios, sheet_name="Materias")
aulas_df = pd.read_excel(archivoLaboratorios, sheet_name="Aulas")
pa_df = pd.read_excel(archivoPA, sheet_name="Data")

pa_full = pa_df_raw = pd.read_excel(archivoPA, sheet_name="Data")
pa_full["HORA_INICIO"] = pa_full["HORA_INICIO"].apply(corregir_hora)
pa_full["HORA_FIN"] = pa_full["HORA_FIN"].apply(corregir_hora)
pa_full["SALA"] = pa_full["SALA"].astype(str).str.strip()
pa_full = pa_full[pa_full["PERIODO"] == 202520]

# Formato y filtrado
pa_df["HORA_INICIO"] = pa_df["HORA_INICIO"].apply(corregir_hora)
pa_df["HORA_FIN"] = pa_df["HORA_FIN"].apply(corregir_hora)
pa_df["SALA"] = pa_df["SALA"].astype(str).str.strip()
pa_df = pa_df[
    (pa_df["PERIODO"] == 202520)
    & (pa_df["SSBSECT_SCHD_CODE"] == "PRA")
    & (pa_df["EDIFICIO"].isin(["UPE", "UPO"]))
]

# Cupos
cupos_dict = dict(zip(aulas_df["CodSala"], aulas_df["Cupo"]))
aulas_disponibles = sorted(pa_df["SALA"].unique())

# Selección de aula
aula = st.selectbox("🎓 Selecciona un aula", aulas_disponibles)

if aula:
    cupo = cupos_dict.get(aula, 1)
    registros = pa_full[pa_full["SALA"] == aula]
    materias_unicas = sorted(set(registros["MATERIA_TITULO_PA"]))

    franjas = [
        ("07:00", "08:00"),
        ("08:05", "09:05"),
        ("09:10", "10:10"),
        ("10:15", "11:15"),
        ("11:20", "12:20"),
        ("12:25", "13:25"),
        ("13:30", "14:30"),
        ("14:35", "15:35"),
        ("15:40", "16:40"),
        ("16:45", "17:45"),
        ("17:50", "18:50"),
        ("18:55", "19:55"),
        ("20:00", "21:00"),
        ("21:05", "21:50"),
    ]
    franjas_labels = [f"{ini}-{fin}" for ini, fin in franjas]
    dias = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes"}
    dias_inverso = {v: k for k, v in dias.items()}

    # Asignar color base a cada materia
    materia_colores = {}
    colores_base = qualitative.Bold
    for i, mat in enumerate(materias_unicas):
        rgb_str = colores_base[i % len(colores_base)]  # ejemplo: 'rgb(127, 60, 141)'
        rgb_values = tuple(int(x.strip()) / 255 for x in rgb_str[4:-1].split(","))  # (0.5, 0.3, 0.7)
        materia_colores[mat] = to_hex(rgb_values)


    # Construir matrices para graficar
    z_matrix, color_matrix, text_matrix = [], [], []

    for dia_nombre in dias.values():
        fila_z = []
        fila_colors = []
        fila_texts = []

        for ini, fin in franjas:
            franja_label = f"{ini}-{fin}"
            match = registros[
                (registros["HORA_INICIO"] == ini)
                & (registros["HORA_FIN"] == fin)
                & (registros["DAY_ID"] == dias_inverso[dia_nombre])
            ]

            if not match.empty:
                row   = match.iloc[0]
                materia = row["MATERIA_TITULO_PA"]
                inscritos = row["INSCRITOS"]
                ocup   = min(inscritos / cupo, 1.0)
                color_base = materia_colores.get(materia, "#cccccc")
                color_rgba = aplicar_tonalidad(color_base, ocup)
                print(f"{materia} - ocupación: {ocup:.2f} → color: {color_rgba}")
                fila_z.append(ocup)
                fila_colors.append(color_rgba)
                fila_texts.append(
                    f"<b>{materia}</b><br>"
                    f"Cupo: {cupo}<br>"
                    f"Inscritos: {inscritos}<br>"
                    f"Ocupación: {ocup:.0%}"
                )
            else:
                fila_z.append(0)
                fila_colors.append("rgba(0,0,0,0.7)")  # verde para disponible
                fila_texts.append(f"Disponible<br>Cupo: {cupo}")

        z_matrix.append(fila_z)
        color_matrix.append(fila_colors)
        text_matrix.append(fila_texts)

    # Crear figura con plotly
    fig = go.Figure()

    # Capa invisible solo para los tooltips
    fig.add_trace(
        go.Heatmap(
            z=[[0 for _ in franjas_labels] for _ in dias.values()],  # Dummy values
            x=franjas_labels,
            y=list(dias.values()),
            text=text_matrix,
            hoverinfo="text",
            showscale=False,
            opacity=0.0,  # <-- hace que el Heatmap sea invisible visualmente
            colorscale=[[0, "#ffffff"], [1, "#ffffff"]],
            zmin=0,
            zmax=1,
        )
    )

    # Pintar cada celda con color manual
    for i, y in enumerate(dias.values()):
        for j, x in enumerate(franjas_labels):
            fig.add_shape(
                type="rect",
                x0=j - 0.5,
                y0=i - 0.5,
                x1=j + 0.5,
                y1=i + 0.5,
                line=dict(width=1.5),
                fillcolor=color_matrix[i][j],
                layer="below",
            )

    fig.update_layout(
        title=f"Mapa de Calor Interactivo - Aula {aula}",
        xaxis=dict(title="Franja Horaria", tickmode="array", tickvals=franjas_labels),
        yaxis=dict(
            title="Día",
            autorange="reversed",
            zeroline=False,
            showgrid=False,
            showline=False,
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        height=650,
    )

    # Mostrar app
    col1, col2 = st.columns([4, 1])
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("#### Materias Asignadas")
        for mat in materias_unicas:
            color = materia_colores.get(mat, "#ccc")
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; margin-bottom: 6px;">
                    <div style="width: 16px; height: 16px; background-color: {color}; margin-right: 8px; border-radius: 3px;"></div>
                    <span>{mat}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
