# -----------------------------------------------------------------
# Matriz día × franja con porcentaje de ocupación y control por aula.
# Ejecutar con:
#     streamlit run capacidadesApp_heatmap.py
# -----------------------------------------------------------------
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import os

# ─────────── Primera instrucción Streamlit ─────────── #
st.set_page_config(layout="wide")
# ----------------------------------------------------- #

# ---------------- CONFIGURACIÓN ----------------------- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "db", "Pregrado", "Pregrado PA 2025.xlsx")
PERIODO = "202520"

AULAS = [
    "UPE/417", "UPE/424", "UPO/415", "UPO/410", "UPO/309", "UPO/414",
    "UPO/413", "UPE/416", "UPO/406", "UPO/407", "UPO/408", "UPE/423",
    "UPE/422", "UPO/403", "UPO/402", "UPE/421", "UPE/419", "UPE/418",
    "UPE/420"
]

FRANJAS = [
    ("0700", "0800"), ("0805", "0905"), ("0910", "1010"), ("1015", "1115"),
    ("1120", "1220"), ("1225", "1325"), ("1330", "1430"), ("1435", "1535"),
    ("1540", "1640"), ("1645", "1745"), ("1750", "1849"), ("1850", "1949"),
    ("1950", "2049"), ("2050", "2149")
]
FRANJA_LABELS = [f"{ini[:2]}:{ini[2:]}-{fin[:2]}:{fin[2:]}" for ini, fin in FRANJAS]
DAYS_MAP  = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes"}
DAYS_LIST = [DAYS_MAP[i] for i in range(1, 6)]
# ----------------------------------------------------- #

# ---------------- UTILIDADES ------------------------- #
def hhmm_to_min(hhmm: str) -> int:
    hhmm = str(hhmm).zfill(4)
    return int(hhmm[:2]) * 60 + int(hhmm[2:])

FRANJAS_MIN = [(hhmm_to_min(i), hhmm_to_min(f)) for i, f in FRANJAS]
def solapan(r1, r2) -> bool:
    return r1[0] < r2[1] and r2[0] < r1[1]
# ----------------------------------------------------- #

# ---------------- DATOS ------------------------------ #
@st.cache_data(show_spinner=True)
def load_data() -> pd.DataFrame:
    df = pd.read_excel(EXCEL_PATH, dtype=str, sheet_name="Data")
    df = df[df["PERIODO"] == PERIODO]
    df = df[df["SALA"].isin(AULAS)]
    df["DAY_ID"] = pd.to_numeric(df["DAY_ID"], errors="coerce")
    df = df[df["DAY_ID"].between(1, 5)]
    for col in ("HORA_INICIO", "HORA_FIN"):
        df[col] = df[col].astype(str).str.zfill(4)
    df["INI_MIN"] = df["HORA_INICIO"].apply(hhmm_to_min)
    df["FIN_MIN"] = df["HORA_FIN"].apply(hhmm_to_min)
    return df

df_all = load_data()
# ----------------------------------------------------- #

# ---------------- INTERFAZ --------------------------- #
st.title("📋 Matriz de Ocupación de Aulas por Tipo de Sala")

tipos = (
    df_all.loc[df_all["SALA"].isin(AULAS), "TIPO_SALA_DESC"]
    .dropna()
    .sort_values()
    .unique()
)
tipo_sel = st.selectbox("Tipo de sala", tipos)

# Aulas disponibles para ese tipo
aulas_tipo_total = (
    df_all[df_all["TIPO_SALA_DESC"] == tipo_sel]["SALA"]
    .dropna()
    .sort_values()
    .unique()
)

# Columna izquierda y derecha
col1, col2 = st.columns([4, 1])

with col2:
    st.markdown("### Aulas activas")
    aulas_seleccionadas = []
    for aula in aulas_tipo_total:
        checked = st.checkbox(aula, value=True, key=aula)
        if checked:
            aulas_seleccionadas.append(aula)

    st.markdown("---")
    st.markdown(f"**Total seleccionadas:** {len(aulas_seleccionadas)}")

# Filtrar data según selección
df_filtrado = df_all[
    (df_all["TIPO_SALA_DESC"] == tipo_sel) &
    (df_all["SALA"].isin(aulas_seleccionadas))
]

# ---------------- MATRIZ ----------------------------- #
def construir_matriz(df: pd.DataFrame) -> pd.DataFrame:
    matriz = pd.DataFrame("", index=DAYS_LIST, columns=FRANJA_LABELS, dtype=str)
    for idx_day, day_name in enumerate(DAYS_LIST, start=1):
        dia_df = df[df["DAY_ID"] == idx_day]
        if dia_df.empty:
            continue
        for (f_ini, f_fin), label in zip(FRANJAS_MIN, FRANJA_LABELS):
            aulas_ocup = dia_df[
                dia_df.apply(
                    lambda r: solapan((f_ini, f_fin), (r.INI_MIN, r.FIN_MIN)),
                    axis=1,
                )
            ]["SALA"].unique()
            if aulas_ocup.size:
                matriz.at[day_name, label] = ", ".join(sorted(aulas_ocup))
    return matriz

matriz = construir_matriz(df_filtrado)
total_aulas_tipo = len(aulas_seleccionadas)

# ---------------- VISUALIZACIÓN ---------------------- #
z_matrix = []
text_matrix = []
hover_matrix = []

for day in DAYS_LIST:
    fila_z = []
    fila_text = []
    fila_hover = []

    for col in FRANJA_LABELS:
        aulas_ocup = matriz.at[day, col]
        if aulas_ocup.strip() == "":
            ocupadas = 0
            aulas_list = []
        else:
            aulas_list = [a.strip() for a in aulas_ocup.split(",")]
            ocupadas = len(aulas_list)

        porcentaje = ocupadas / total_aulas_tipo if total_aulas_tipo > 0 else 0
        fila_z.append(porcentaje)
        fila_text.append(f"{int(porcentaje * 100)}%")
        hover = f"Ocupadas ({ocupadas}/{total_aulas_tipo}):<br>" + "<br>".join(aulas_list)
        fila_hover.append(hover)

    z_matrix.append(fila_z)
    text_matrix.append(fila_text)
    hover_matrix.append(fila_hover)

fig = go.Figure()

fig.add_trace(go.Heatmap(
    z=z_matrix,
    x=FRANJA_LABELS,
    y=DAYS_LIST,
    text=text_matrix,
    hovertext=hover_matrix,
    hoverinfo="text",
    texttemplate="%{text}",
    colorscale="YlOrRd",
    zmin=0,
    zmax=1,
    colorbar=dict(title="Ocupación"),
    showscale=True,
))

# Agregar bordes de celdas
for i, y in enumerate(DAYS_LIST):
    for j, x in enumerate(FRANJA_LABELS):
        fig.add_shape(
            type="rect",
            x0=j - 0.5,
            x1=j + 0.5,
            y0=i - 0.5,
            y1=i + 0.5,
            line=dict(color="black", width=1),
            xref="x",
            yref="y",
        )

fig.update_layout(
    title=f"Mapa de Calor – Ocupación {tipo_sel}",
    xaxis=dict(title="Franja Horaria", tickmode="array", tickvals=FRANJA_LABELS),
    yaxis=dict(title="Día", autorange="reversed"),
    height=700,
    margin=dict(l=0, r=0, t=50, b=0),
)

with col1:
    st.plotly_chart(fig, use_container_width=True)
