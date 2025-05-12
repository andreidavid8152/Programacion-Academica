import pandas as pd
from collections import defaultdict

# Archivos
archivoLaboratorios = "db/Laboratorios.xlsx"
archivoPA = "db/pregrado/Pregrado PA 2025.xlsx"

# Cargar datos
materias_df = pd.read_excel(archivoLaboratorios, sheet_name="Materias")
aulas_df = pd.read_excel(archivoLaboratorios, sheet_name="Aulas")
pa_df = pd.read_excel(archivoPA, sheet_name="Data")

# Crear diccionario de cupos por CodSala
cupos_dict = dict(zip(aulas_df["CodSala"], aulas_df["Cupo"]))

# Filtrar solo las columnas necesarias
materias_df = materias_df[["ID CARRERA", "NOMBRE", "SEMESTRE"]]
materias_dicts = materias_df.to_dict(orient="records")

# Agrupar por ID CARRERA
grupos_carrera = defaultdict(list)
for item in materias_dicts:
    grupos_carrera[item["ID CARRERA"]].append(item)

# Recorrer cada grupo y agregar aulas únicas con su capacidad
for id_carrera, lista_materias in grupos_carrera.items():
    for materia in lista_materias:
        nombre_materia = materia["NOMBRE"]

        # Filtrar PA
        filtro = (
            (pa_df["MATERIA_TITULO_PA"].str.upper() == nombre_materia.upper())
            & (pa_df["PERIODO"] == 202520)
            & (pa_df["SSBSECT_SCHD_CODE"] == "PRA")
            & (pa_df["EDIFICIO"].isin(["UPE", "UPO"]))
        )

        # Filtrar aulas, excluyendo las vacías o incorrectas
        aulas_validas = pa_df.loc[filtro, "SALA"].dropna()
        aulas_validas = aulas_validas[aulas_validas != "/"].unique().tolist()

        # Crear lista de aulas con su capacidad
        aulas_con_cupo = []
        for aula in aulas_validas:
            capacidad = cupos_dict.get(aula, None)  # Puede no existir en la hoja Aulas
            aulas_con_cupo.append({"SALA": aula, "CUPO": capacidad})

        materia["AULAS"] = aulas_con_cupo

# Imprimir resultados
for id_carrera, lista_materias in grupos_carrera.items():
    print(f"\nID CARRERA: {id_carrera}")
    for materia in lista_materias:
        print(materia)


# Obtener todas las aulas únicas usadas en todos los diccionarios
aulas_totales = set()

for lista_materias in grupos_carrera.values():
    for materia in lista_materias:
        for aula in materia.get("AULAS", []):
            nombre_sala = aula.get("SALA")
            if nombre_sala and nombre_sala != "/":
                aulas_totales.add(nombre_sala)
                
# Convertir a lista (opcional, si quieres ordenarlas también)
aulas_unicas = sorted(list(aulas_totales))

print("\n🔹 AULAS ÚNICAS USADAS EN TODAS LAS MATERIAS:")
for aula in aulas_unicas:
    print(aula)
