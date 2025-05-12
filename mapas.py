import pandas as pd
import matplotlib

matplotlib.use("Agg")  # Usar backend no interactivo
import matplotlib.pyplot as plt
import seaborn as sns
import os
from collections import defaultdict

# Archivos
archivoLaboratorios = "db/Laboratorios.xlsx"
archivoPA = "db/pregrado/Pregrado PA 2025.xlsx"

# Cargar datos
materias_df = pd.read_excel(archivoLaboratorios, sheet_name="Materias")
aulas_df = pd.read_excel(archivoLaboratorios, sheet_name="Aulas")
pa_df = pd.read_excel(archivoPA, sheet_name="Data")

# Diccionario de cupos
cupos_dict = dict(zip(aulas_df["CodSala"], aulas_df["Cupo"]))

# Procesar materias
materias_df = materias_df[["ID CARRERA", "NOMBRE", "SEMESTRE"]]
materias_dicts = materias_df.to_dict(orient="records")

grupos_carrera = defaultdict(list)
for item in materias_dicts:
    grupos_carrera[item["ID CARRERA"]].append(item)

# Enriquecer materias con aulas
for id_carrera, lista_materias in grupos_carrera.items():
    for materia in lista_materias:
        nombre_materia = materia["NOMBRE"]

        filtro = (
            (pa_df["MATERIA_TITULO_PA"].str.upper() == nombre_materia.upper())
            & (pa_df["PERIODO"] == 202520)
            & (pa_df["SSBSECT_SCHD_CODE"] == "PRA")
            & (pa_df["EDIFICIO"].isin(["UPE", "UPO"]))
        )

        aulas_validas = pa_df.loc[filtro, "SALA"].dropna()
        aulas_validas = aulas_validas[aulas_validas != "/"].unique().tolist()

        aulas_con_cupo = []
        for aula in aulas_validas:
            capacidad = cupos_dict.get(aula, None)
            aulas_con_cupo.append({"SALA": aula, "CUPO": capacidad})

        materia["AULAS"] = aulas_con_cupo

# Extraer aulas únicas usadas
aulas_totales = set()
for lista_materias in grupos_carrera.values():
    for materia in lista_materias:
        for aula in materia.get("AULAS", []):
            nombre_sala = aula.get("SALA")
            if nombre_sala and nombre_sala != "/":
                aulas_totales.add(nombre_sala)

aulas_unicas = sorted(list(aulas_totales))

# Definición de franjas horarias y días
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

# Corregir formatos de hora: convertir "1750" a "17:50"
def corregir_hora(h):
    h = str(h).zfill(4)  # Asegura 4 dígitos, ej. 905 -> 0905
    return h[:2] + ":" + h[2:]

pa_df["HORA_INICIO"] = pa_df["HORA_INICIO"].apply(corregir_hora)
pa_df["HORA_FIN"] = pa_df["HORA_FIN"].apply(corregir_hora)


# Carpeta de salida
os.makedirs("mapas_aulas", exist_ok=True)

# Solo generar para aulas_unicas
for aula in aulas_unicas:
    cupo = cupos_dict.get(aula)
    if not cupo or cupo == 0:
        continue

    # Crear matriz: filas = días, columnas = franjas
    matriz_valores = pd.DataFrame("", index=list(dias.values()), columns=franjas_labels)
    registros = pa_df[pa_df["SALA"] == aula]

    for _, row in registros.iterrows():
        dia = dias.get(row["DAY_ID"])
        if not dia:
            continue
        h_inicio = row["HORA_INICIO"]
        h_fin = row["HORA_FIN"]
        inscritos = row["INSCRITOS"]
        materia = row["MATERIA_TITULO_PA"]

        for i, (ini, fin) in enumerate(franjas):
            if h_inicio == ini and h_fin == fin:
                franja_label = f"{ini}-{fin}"
                ocupacion = min(inscritos / cupo, 1.0)
                texto = f"{materia}\n{ocupacion:.0%}"
                matriz_valores.at[dia, franja_label] = texto
                break

    # Crear mapa de calor vacío (solo para los colores)
    matriz_ocupacion = pd.DataFrame(
        0.0, index=list(dias.values()), columns=franjas_labels
    )
    for _, row in registros.iterrows():
        dia = dias.get(row["DAY_ID"])
        if not dia:
            continue
        h_inicio = row["HORA_INICIO"]
        h_fin = row["HORA_FIN"]
        inscritos = row["INSCRITOS"]

        for i, (ini, fin) in enumerate(franjas):
            if h_inicio == ini and h_fin == fin:
                franja_label = f"{ini}-{fin}"
                matriz_ocupacion.at[dia, franja_label] = min(inscritos / cupo, 1.0)
                break

    # Generar heatmap con anotaciones de materia
    # Obtener materias únicas asignadas al aula
    materias_unicas = sorted(set(registros["MATERIA_TITULO_PA"]))

    # Crear figura con dos subplots: uno para el heatmap, otro para la lista
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(16, 6), gridspec_kw={"width_ratios": [4, 1]}
    )

    # Heatmap
    sns.heatmap(
        matriz_ocupacion,
        annot=matriz_valores,
        fmt="",
        cmap="YlOrRd",
        cbar_kws={"label": "Ocupación"},
        linewidths=0.5,
        linecolor="lightgray",
        ax=ax1,
    )
    ax1.set_title(f"Mapa de Calor - Aula {aula}")
    ax1.set_xlabel("Franja Horaria")
    ax1.set_ylabel("Día de la Semana")
    ax1.tick_params(axis="x", rotation=45)

    # Lista de materias
    ax2.axis("off")
    materias_texto = "\n".join(f"• {m}" for m in materias_unicas)
    ax2.text(0, 1, f"Materias en\n{aula}:\n\n{materias_texto}", fontsize=10, va="top")

    # Guardar figura
    plt.tight_layout()
    plt.savefig(f"mapas_aulas/heatmap_{aula.replace('/', '_')}.png")
    plt.close()
