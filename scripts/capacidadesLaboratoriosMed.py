import pandas as pd

def capacidadesLaboratoriosMed():
    # -------------------- CONFIG -------------------- #
    EXCEL_PATH = "db/Pregrado/Pregrado PA 2025.xlsx"
    PERIODO = "202520"

    AULAS = [
        "UPE/417",
        "UPE/424",
        "UPO/415",
        "UPO/410",
        "UPO/309",
        "UPO/414",
        "UPO/413",
        "UPE/416",
        "UPO/406",
        "UPO/407",
        "UPO/408",
        "UPE/423",
        "UPE/422",
        "UPO/403",
        "UPO/402",
        "UPE/421",
        "UPE/419",
        "UPE/418",
        "UPE/420",
    ]

    FRANJAS = [
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
        ("2050", "2149"),
    ]
    # ------------------------------------------------ #

    # --- utilidades tiempo --- #
    def hhmm_to_min(hhmm: str) -> int:
        hhmm = str(hhmm).zfill(4)  # ‘830’ → ‘0830’
        return int(hhmm[:2]) * 60 + int(hhmm[2:])

    FRANJAS_MIN = [(hhmm_to_min(i), hhmm_to_min(f)) for i, f in FRANJAS]

    def solapan(r1, r2):  # (ini1,fin1) vs (ini2,fin2)
        return r1[0] < r2[1] and r2[0] < r1[1]

    # --- carga y limpieza --- #
    df = pd.read_excel(EXCEL_PATH, dtype=str)

    df = df[df["PERIODO"] == PERIODO]  # 1) periodo
    df["DAY_ID"] = pd.to_numeric(df["DAY_ID"], errors="coerce")
    df = df[df["DAY_ID"].between(1, 5)]  # 2) lunes-viernes

    # horas como texto siempre de 4 dígitos
    for col in ("HORA_INICIO", "HORA_FIN"):
        df[col] = df[col].astype(str).str.zfill(4)

    df["INI_MIN"] = df["HORA_INICIO"].apply(hhmm_to_min)
    df["FIN_MIN"] = df["HORA_FIN"].apply(hhmm_to_min)

    TOTAL_SLOTS = len(FRANJAS) * 5  # 14 franjas × 5 días = 70

    # --- cálculo de ocupación --- #
    res = []
    for aula in AULAS:
        ocupados = 0
        sub = df[df["SALA"] == aula]

        for dia in range(1, 6):  # lunes=1 … viernes=5
            dia_sub = sub[sub["DAY_ID"] == dia]
            for f_ini, f_fin in FRANJAS_MIN:
                if any(
                    solapan((f_ini, f_fin), (r.INI_MIN, r.FIN_MIN))
                    for _, r in dia_sub.iterrows()
                ):
                    ocupados += 1

        res.append({"Aula": aula, "Porcentaje Ocupacion": ocupados * 100 / TOTAL_SLOTS})

    # --- salida --- #
    out = pd.DataFrame(res).sort_values("Aula")
    print(out.to_string(index=False, formatters={"Porcentaje Ocupacion": "{:.2f}%".format}))
