'''
def simulacionIngresoDiferido():

    # Ver cuantos bloques de (32 personas) podemos crear respecto a las materias de Laboratorio de cada semestre, osea cada bloque sera respecto al semestre, las horas de practica de las materias de laboratorio se divide en horas de practica y de teoria, esta ultima no se deberia tomar en cuenta para esta simulacion, otro aspecto a tomar en cuenta es que se deberia generar el doble de horas practicas de la cantidd normal para generar un bloque, debido a que las aulas de este tipo de materias y en concreto de las horas practicas tiene una capacidad de 16 personas (MITAD).

    """

    Pasos a seguir para generar esta simulacion:

    1. Ir al excel db/Laboratorios -> dirigirse a la hoja 'Simulacion' -> filtrar la columna 'Tipo' = PRA (con esto estamos filtrando unicamente las aulas que se utilizan para las horas practicas de una materia en especifico)

    2. Ahora por cada materia de un semestre, con los datos de las aulas de cada materia (el nombre de la materia esta en la columna MATERIA, las aulas en AULA y el semestre en SEMESTRE), vamos a dirigirnos al excel  (pregrado/Pregrado PA 2025), donde por cada aula respectiva a cada materia vamos a filtrar el aula en la columna 'SALA' y 'PERIODO' = 202520, como en este excel tenemos las horas de todas las materias durante todo un semestre, al filtrar la informacion vamos a poder ver el uso durante toda la semana del aula filtrado, la informacion del dia esta en 'DAY_ID', y la hora de inicio y fin en 'HORA_INICIO' - 'HORA_FIN'.

    3. Ahora ya sabes la disponibiliad de las aulas de cada materia con esto quiero que generes los bloques para cada semestre con respecto a las materias de tipo de laboratorio en un excel, donde cada hoja hace referencia a los bloques generados para cada semestre, y dentro en cada hoja debe estar las siguientes columnas:
    BLOQUE - MATERIA - DIA - HORA INICIO - HORA FIN
    cada registro aqui hace referencia a una sola hora.

    4. Datos a tomar en cuenta debes generar los mismos bloques tanto para el primer semestre como para el segundo
       Las horas de clase estan conformadas de esta manera:
        0700	0800
        0805	0905
        0910	1010
        1015	1115
        1120	1220
        1225	1325
        1330	1430
        1435	1535
        1540	1640
        1645	1745
        1750	1849
        1850	1949
        1950	2049
        2050	2149
        2150	2249
        2250	2349

        Spoiler las materias a evaluar son las siguientes solo te paso esta informacion porque no tienes cuantas horas a la semana tiene una materia (para las materias que tienen mas de una hora en este caso dos horas pues debe tener como aspecto primordial que sean seguidas las horas):

        Anatomia Clinica e Imagenlogia I | horas practicas => 2 horas

        Anatomia Clinica e Imagenlogia II | horas practicas => 2 horas

        Embriologia | horas practicas => 1 hora

        Neuroanatomia | horas practicas => 1 hora


    """
    #

    return
'''

import pandas as pd
from collections import defaultdict
import re


def simulacionIngresoDiferido():
    print("🔄 Iniciando simulacionIngresoDiferido()")

    # ───────── utilidades ─────────
    def str_to_min(t):
        s = str(int(t)) if not isinstance(t, str) else t
        s = s.zfill(4)
        return int(s[:2]) * 60 + int(s[2:])

    def min_to_str(m):
        h, mm = divmod(m, 60)
        return f"{h:02d}{mm:02d}"

    def normalize_name(s):
        return re.sub(r"[^a-z0-9]", "", s.lower())

    # ───────── franjas horarias ─────────
    franjas = [
        ("0700", "0800"),
        ("0805", "0905"),
        ("0910", "1010"),
        ("1015", "1115"),
        ("1120", "1220"),
        ("1225", "1325"),
        ("1330", "1430"),
        ("1435", "1535"),
        ("1540", "1640"),
        ("1645", "1745"),
        ("1750", "1849"),
        ("1850", "1949"),
        ("1950", "2049"),
        ("2050", "2149")
    ]
    horarios = [(str_to_min(s), str_to_min(e)) for s, e in franjas]

    # ───────── horas prácticas ─────────
    practicas = {
        "D-ANATOM CLINIC E IMAGENOL I": 2,
        "D-ANATOM CLINIC E IMAGENOL II": 2,
        "D-EMBRIOLOGIA": 1,
        "D-NEUROANATOMIA": 1,
    }
    norm_pract = {normalize_name(k): v for k, v in practicas.items()}

    # ───────── datos ─────────
    df_labs = pd.read_excel("db/Laboratorios.xlsx", sheet_name="Simulacion")
    df_labs = df_labs[df_labs["TIPO"] == "PRA"]

    df_uso = pd.read_excel("db/pregrado/Pregrado PA 2025.xlsx")
    df_uso = df_uso[df_uso["PERIODO"] == 202520]

    resultados = {}
    min_bloques = float("inf")

    # reservas globales: (aula, dia, idx_franja)
    usados_global: set[tuple[str, int, int]] = set()

    # lunes-viernes (1-5)  ──  agrega 6 ó 7 si deseas sábado/domingo
    dia_rotacion = [1, 2, 3, 4, 5]

    # ───────── proceso por semestre ─────────
    for semestre in sorted(df_labs["SEMESTRE"].unique()):
        materias_sem = df_labs[df_labs["SEMESTRE"] == semestre]["MATERIA"].unique()
        materias_info = {}

        for materia in materias_sem:
            aulas = (
                df_labs[
                    (df_labs["MATERIA"] == materia) & (df_labs["SEMESTRE"] == semestre)
                ]["AULA"]
                .unique()
                .tolist()
            )
            horas = norm_pract.get(normalize_name(materia), 0)
            if horas == 0:
                continue
            materias_info[materia] = {"aulas": aulas, "horas": horas}

        # disponibilidad aula-día-franja
        disponibilidad = defaultdict(lambda: defaultdict(list))
        for aula in df_labs[df_labs["SEMESTRE"] == semestre]["AULA"].unique():
            ocupaciones = df_uso[df_uso["SALA"] == aula]
            for dia in range(1, 8):
                ocup = [
                    (str_to_min(i), str_to_min(f))
                    for i, f in ocupaciones[ocupaciones["DAY_ID"] == dia][
                        ["HORA_INICIO", "HORA_FIN"]
                    ].values
                ]
                libres = [
                    idx
                    for idx, (i, f) in enumerate(horarios)
                    if all(f <= oi or i >= of for oi, of in ocup)
                ]
                disponibilidad[aula][dia] = libres

        bloques = []
        bloque_num = 1

        while True:
            bloque_filas = []
            # ► días ya usados por CADA grupo en el bloque actual
            dias_usados_por_grupo = {1: set(), 2: set()}
            franjas_usadas_en_bloque: set[tuple[str, int, int]] = set()
            exito_bloque = True

            for materia, info in materias_info.items():
                horas_base = info["horas"]
                aulas_disp = info["aulas"]

                # se agenda grupo 1 y luego grupo 2
                for grupo in (1, 2):
                    asignado = False
                    for dia in dia_rotacion:
                        # ⛔ ya hay otra materia de ESTE grupo ese día
                        if dia in dias_usados_por_grupo[grupo]:
                            continue
                        for aula in aulas_disp:
                            libres_tot = disponibilidad[aula][dia]
                            libres = [
                                idx
                                for idx in libres_tot
                                if (aula, dia, idx) not in usados_global
                                and (aula, dia, idx) not in franjas_usadas_en_bloque
                            ]
                            libres.sort()

                            # buscar 'horas_base' franjas contiguas
                            for i in range(len(libres) - horas_base + 1):
                                if all(
                                    libres[i + k] == libres[i] + k
                                    for k in range(horas_base)
                                ):
                                    # reserva exitosa
                                    for k in range(horas_base):
                                        idx_slot = libres[i + k]
                                        start, end = horarios[idx_slot]
                                        franjas_usadas_en_bloque.add(
                                            (aula, dia, idx_slot)
                                        )
                                        bloque_filas.append(
                                            {
                                                "BLOQUE": bloque_num,
                                                "GRUPO": grupo,
                                                "MATERIA": materia,
                                                "AULA": aula,
                                                "DIA": dia,
                                                "HORA INICIO": min_to_str(start),
                                                "HORA FIN": min_to_str(end),
                                            }
                                        )
                                    dias_usados_por_grupo[grupo].add(dia)
                                    asignado = True
                                    break
                            if asignado:
                                break
                        if asignado:
                            break

                    if not asignado:
                        exito_bloque = False
                        break  # no se pudo completar el bloque

                if not exito_bloque:
                    break

            if not exito_bloque:
                break

            # consolidar reservas en el mapa global
            usados_global.update(franjas_usadas_en_bloque)
            bloques.extend(bloque_filas)
            bloque_num += 1

        resultados[semestre] = bloques
        min_bloques = min(min_bloques, bloque_num - 1)

    # ───────── exportar a Excel ─────────
    with pd.ExcelWriter("simulacion_ingreso_diferido.xlsx") as writer:
        for semestre, filas in resultados.items():
            df = pd.DataFrame(filas)
            df = df[df["BLOQUE"] <= min_bloques]
            df = df.sort_values(by=["BLOQUE", "GRUPO", "DIA", "HORA INICIO"])
            df.to_excel(writer, sheet_name=f"Semestre_{semestre}", index=False)

    print("✅ simulacion_ingreso_diferido.xlsx generado")

