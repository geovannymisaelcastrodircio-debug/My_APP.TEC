# ======================= IMPORTS =======================
import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import date
import re

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
        st.dataframe(df_all_data[["NOMBRE_(S)", "A._PAT", "A._MAT", "NUM.CONTROL"]])

        # Búsqueda por nombre
        busqueda_nombre = st.text_input("Escribe el nombre del estudiante:")
        if busqueda_nombre:
            resultados = []
            for carrera in carreras:
                coleccion = db[carrera]
                query = {"NOMBRE_(S)": {"$regex": busqueda_nombre.strip(), "$options": "i"}}
                resultados.extend(list(coleccion.find(query, {"_id": 0})))
            if resultados:
                df_resultados = pd.DataFrame(resultados)
                st.dataframe(df_resultados[["NOMBRE_(S)", "A._PAT", "A._MAT", "NUM.CONTROL"]])
                seleccion = st.selectbox("Selecciona un estudiante:", df_resultados["NOMBRE_(S)"].tolist())
                if seleccion:
                    fila = df_resultados[df_resultados["NOMBRE_(S)"] == seleccion].iloc[0]
                    st.json(fila.to_dict())
            else:
                st.info("No se encontraron coincidencias por nombre.")

        # Búsqueda por número de control
        busqueda_num = st.text_input("Escribe el número de control:")
        if busqueda_num:
            # Normalizar el número de control
            num_input = re.sub(r'\D', '', busqueda_num.strip())
            num_normalizado = int(num_input) if num_input.isdigit() else num_input

            resultados = []
            for carrera in carreras:
                coleccion = db[carrera]
                query = {
                    "$or": [
                        {"NUM.CONTROL": num_normalizado},
                        {"NUM.CONTROL": {"$regex": f"^{num_input}$", "$options": "i"}}
                    ]
                }
                resultados.extend(list(coleccion.find(query, {"_id": 0})))

            if resultados:
                df_resultados = pd.DataFrame(resultados)
                st.dataframe(df_resultados[["NOMBRE_(S)", "A._PAT", "A._MAT", "NUM.CONTROL"]])
                seleccion = st.selectbox("Selecciona un estudiante:", df_resultados["NOMBRE_(S)"].tolist())
                if seleccion:
                    fila = df_resultados[df_resultados["NOMBRE_(S)"] == seleccion].iloc[0]
                    st.json(fila.to_dict())
            else:
                st.warning("⚠️ No se encontraron coincidencias para ese número de control.")

    # ======================= 2. VER ALUMNOS POR CARRERA =======================
    elif menu == "📖 Ver Alumnos por Carrera":
        st.subheader("📖 Ver Alumnos por Carrera")
        carrera = st.selectbox("Selecciona carrera:", carreras)
        if carrera:
            coleccion = db[carrera]
            df_carrera = pd.DataFrame(list(coleccion.find({}, {"_id": 0})))
            if not df_carrera.empty:
                df_carrera["NOMBRE_COMPLETO"] = (
                    df_carrera.get("NOMBRE_(S)", pd.Series([""]*len(df_carrera))).fillna("") + " " +
                    df_carrera.get("A._PAT", pd.Series([""]*len(df_carrera))).fillna("") + " " +
                    df_carrera.get("A._MAT", pd.Series([""]*len(df_carrera))).fillna("")
                )
                st.dataframe(df_carrera[["NOMBRE_COMPLETO", "NUM.CONTROL"]])
                seleccion = st.selectbox("Selecciona un estudiante:", df_carrera["NOMBRE_COMPLETO"].tolist())
                if seleccion:
                    fila = df_carrera[df_carrera["NOMBRE_COMPLETO"] == seleccion].iloc[0]
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
                            df_periodo.get("NOMBRE_(S)", pd.Series([""]*len(df_periodo))).fillna("") + " " +
                            df_periodo.get("A._PAT", pd.Series([""]*len(df_periodo))).fillna("") + " " +
                            df_periodo.get("A._MAT", pd.Series([""]*len(df_periodo))).fillna("")
                        )
                        estudiante = st.selectbox("Selecciona un estudiante:", df_periodo["NOMBRE_COMPLETO"].tolist())
                        if estudiante:
                            fila = df_periodo[df_periodo["NOMBRE_COMPLETO"] == estudiante].iloc[0]
                            st.json(fila.to_dict())

                            st.markdown("---")
                            st.subheader("✏️ Editar datos del estudiante")
                            nombre = st.text_input("Nombre(s)", value=fila.get("NOMBRE_(S)", ""))
                            apellido_pat = st.text_input("Apellido Paterno", value=fila.get("A._PAT", ""))
                            apellido_mat = st.text_input("Apellido Materno", value=fila.get("A._MAT", ""))
                            num_control = st.text_input("Número de control", value=str(fila.get("NUM.CONTROL", "")))
                            sexo = st.text_input("Sexo", value=fila.get("SEXO", ""))
                            tema = st.text_area("Tema", value=fila.get("TEMA", ""))
                            asesor_interno = st.text_input("Asesor Interno", value=fila.get("A._INTERNO", ""))
                            asesor_externo = st.text_input("Asesor Externo", value=fila.get("A._EXTERNO", ""))
                            revisor = st.text_input("Revisor", value=fila.get("REVISOR", ""))
                            observaciones = st.text_area("Observaciones", value=fila.get("OBSERVACIONES", ""))

                            fecha_str = fila.get("FECHA_DICTAMEN", None)
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
                                    {"NUM.CONTROL": fila.get("NUM.CONTROL", ""), "PERIODO": periodo},
                                    {"$set": {
                                        "NOMBRE_(S)": nombre,
                                        "A._PAT": apellido_pat,
                                        "A._MAT": apellido_mat,
                                        "NUM.CONTROL": int(num_control.strip()) if num_control.strip().isdigit() else num_control,
                                        "SEXO": sexo,
                                        "TEMA": tema,
                                        "A._INTERNO": asesor_interno,
                                        "A._EXTERNO": asesor_externo,
                                        "REVISOR": revisor,
                                        "OBSERVACIONES": observaciones,
                                        "FECHA_DICTAMEN": str(fecha_dictamen),
                                        "NOMBRE_COMPLETO": f"{nombre} {apellido_pat} {apellido_mat}".strip()
                                    }}
                                )
                                st.success(f"✅ Estudiante '{nombre} {apellido_pat}' actualizado correctamente.")
                                st.rerun()
