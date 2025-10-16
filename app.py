# ======================= IMPORTS =======================
import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import date

# ======================= CONFIGURACIÓN =======================
st.set_page_config(page_title="Sistema de Estudiantes", page_icon="🎓", layout="wide")

# ======================= USUARIOS =======================
USERS = {
    "admin": "1234",
    "misa": "CADAN09"
}

# ======================= SESIÓN =======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""

# ======================= LOGIN =======================
if not st.session_state.logged_in:
    st.title("🔐 Inicio de Sesión")
    usuario_input = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if usuario_input in USERS and password == USERS[usuario_input]:
            st.session_state.logged_in = True
            st.session_state.usuario = usuario_input
            st.success("✅ Acceso concedido")
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos")

# ======================= APP PRINCIPAL =======================
else:
    # ======================= CONEXIÓN MONGODB =======================
    client = MongoClient(
        "mongodb+srv://MISACAST:CADAN09@estudiantes.ddelcua.mongodb.net/?retryWrites=true&w=majority&appName=ESTUDIANTES",
        connect=True,
        serverSelectionTimeoutMS=3000
    )
    db = client["ARCHIVOS-RESIDENCIAS"]

    # ✅ Colecciones corregidas
    carreras = ["I.I", "I.S.C"]

    # ======================= SIDEBAR =======================
    st.sidebar.title(f"Usuario: {st.session_state.usuario}")
    if st.sidebar.button("🚪 Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.usuario = ""
        st.rerun()

    st.sidebar.markdown("### Menú de Navegación")
    menu = st.sidebar.radio("Selecciona opción:", [
        "🔍 Buscar por Nombre o Número de Control",
        "📖 Ver Alumnos por Carrera",
        "📖 Ver / Editar estudiantes"
    ])

    # ======================= 1. BUSCAR POR NOMBRE O NÚMERO DE CONTROL =======================
    if menu == "🔍 Buscar por Nombre o Número de Control":
        st.subheader("🔍 Buscar estudiantes por Nombre o Número de Control")

        # Cargar todos los datos registrados
        all_data = []
        for carrera in carreras:
            coleccion = db[carrera]
            all_data.extend(list(coleccion.find({}, {"_id": 0})))
        df_all_data = pd.DataFrame(all_data)

        # Filtrar registros sin nombre o número de control
        df_all_data = df_all_data.dropna(subset=["NOMBRE (S)", "NUM. CONTROL"])

        # Verificar que las columnas existen
        columns_to_check = ["NOMBRE (S)", "A. PAT", "A. MAT", "NUM. CONTROL"]
        for col in columns_to_check:
            if col not in df_all_data.columns:
                st.error(f"La columna '{col}' no existe en el DataFrame.")
                st.stop()

        # Mostrar la tabla
        st.dataframe(df_all_data[columns_to_check])

    # ======================= 2. VER ALUMNOS POR CARRERA =======================
    elif menu == "📖 Ver Alumnos por Carrera":
        st.subheader("📖 Ver Alumnos por Carrera")

        # Botones para seleccionar carrera
        col1, col2 = st.columns(2)
        if col1.button("Ingeniería en Informática (I.I)"):
            carrera = "I.I"
        elif col2.button("Ingeniería en Sistemas Computacionales (I.S.C)"):
            carrera = "I.S.C"
        else:
            st.stop()

        if carrera:
            coleccion = db[carrera]
            periodos = coleccion.distinct("PERIODO")
            if periodos:
                periodo = st.selectbox("Selecciona periodo:", periodos)
                if periodo:
                    df_periodo = pd.DataFrame(list(coleccion.find({"PERIODO": periodo}, {"_id": 0})))

                    # Filtrar registros sin nombre o número de control
                    df_periodo = df_periodo.dropna(subset=["NOMBRE (S)", "NUM. CONTROL"])

                    if not df_periodo.empty:
                        df_periodo["NOMBRE_COMPLETO"] = (
                            df_periodo.get("NOMBRE (S)", pd.Series([""]*len(df_periodo))).fillna("") + " " +
                            df_periodo.get("A. PAT", pd.Series([""]*len(df_periodo))).fillna("") + " " +
                            df_periodo.get("A. MAT", pd.Series([""]*len(df_periodo))).fillna("")
                        )

                        # Mostrar la tabla con nombre completo y número de control
                        st.dataframe(df_periodo[["NOMBRE_COMPLETO", "NUM. CONTROL"]])

                        # Seleccionar un estudiante
                        estudiante = st.selectbox("Selecciona un estudiante:", df_periodo["NOMBRE_COMPLETO"].tolist())

                        # Botón para mostrar datos completos del estudiante
                        if st.button("Mostrar Datos Completos"):
                            fila = df_periodo[df_periodo["NOMBRE_COMPLETO"] == estudiante].iloc[0]
                            st.json(fila.to_dict())

    # ======================= 3. VER / EDITAR ESTUDIANTES =======================
    elif menu == "📖 Ver / Editar estudiantes":
        st.subheader("📖 Consultar y editar estudiantes por carrera y periodo")
        carrera = st.selectbox("Selecciona carrera:", carreras)
        if carrera:
            coleccion = db[carrera]
            periodos = coleccion.distinct("PERIODO")
            if periodos:
                periodo = st.selectbox("Selecciona periodo:", periodos)
                if periodo:
                    df_periodo = pd.DataFrame(list(coleccion.find({"PERIODO": periodo}, {"_id": 0})))
                    if not df_periodo.empty:
                        df_periodo["NOMBRE_COMPLETO"] = (
                            df_periodo.get("NOMBRE (S)", pd.Series([""]*len(df_periodo))).fillna("") + " " +
                            df_periodo.get("A. PAT", pd.Series([""]*len(df_periodo))).fillna("") + " " +
                            df_periodo.get("A. MAT", pd.Series([""]*len(df_periodo))).fillna("")
                        )
                        estudiante = st.selectbox("Selecciona un estudiante:", df_periodo["NOMBRE_COMPLETO"].tolist())
                        if estudiante:
                            fila = df_periodo[df_periodo["NOMBRE_COMPLETO"] == estudiante].iloc[0]
                            st.json(fila.to_dict())

                            st.markdown("---")
                            st.subheader("✏️ Editar datos del estudiante")
                            nombre = st.text_input("Nombre(s)", value=fila.get("NOMBRE (S)", ""))
                            apellido_pat = st.text_input("Apellido Paterno", value=fila.get("A. PAT", ""))
                            apellido_mat = st.text_input("Apellido Materno", value=fila.get("A. MAT", ""))
                            num_control = st.text_input("Número de control", value=str(fila.get("NUM. CONTROL", "")))
                            sexo = st.text_input("Sexo", value=fila.get("SEXO", ""))
                            tema = st.text_area("Tema", value=fila.get("TEMA", ""))
                            asesor_interno = st.text_input("Asesor Interno", value=fila.get("A. INTERNO", ""))
                            asesor_externo = st.text_input("Asesor Externo", value=fila.get("A. EXTERNO", ""))
                            revisor = st.text_input("Revisor", value=fila.get("REVISOR", ""))
                            observaciones = st.text_area("Observaciones", value=fila.get("OBSERVACIONES", ""))

                            fecha_str = fila.get("FECHA DICTAMEN", None)
                            fecha_dictamen = pd.to_datetime(fecha_str, errors="coerce")
                            if pd.isna(fecha_dictamen):
                                fecha_dictamen = date.today()
                            fecha_dictamen = st.date_input(
                                "Fecha dictamen",
                                value=fecha_dictamen,
                                min_value=date(1980, 1, 1),
                                max_value=date(2035, 12, 31)
                            )

                            if st.button("💾 Actualizar estudiante"):
                                coleccion.update_one(
                                    {"NUM. CONTROL": fila.get("NUM. CONTROL", ""), "PERIODO": periodo},
                                    {"$set": {
                                        "NOMBRE (S)": nombre,
                                        "A. PAT": apellido_pat,
                                        "A. MAT": apellido_mat,
                                        "NUM. CONTROL": int(num_control.strip()) if num_control.strip().isdigit() else num_control,
                                        "SEXO": sexo,
                                        "TEMA": tema,
                                        "A. INTERNO": asesor_interno,
                                        "A. EXTERNO": asesor_externo,
                                        "REVISOR": revisor,
                                        "OBSERVACIONES": observaciones,
                                        "FECHA DICTAMEN": str(fecha_dictamen),
                                        "NOMBRE_COMPLETO": f"{nombre} {apellido_pat} {apellido_mat}".strip()
                                    }}
                                )
                                st.success(f"✅ Estudiante '{nombre} {apellido_pat}' actualizado correctamente.")
                                st.rerun()
