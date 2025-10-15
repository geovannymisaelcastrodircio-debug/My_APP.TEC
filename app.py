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
        "🔍 Buscar por Nombre",
        "🔍 Buscar por Número de Control",
        "📖 Ver Alumnos por Carrera"
    ])

    # ======================= 1. BUSCAR POR NOMBRE =======================
    if menu == "🔍 Buscar por Nombre":
        st.subheader("🔍 Buscar estudiantes por Nombre")
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

    # ======================= 2. BUSCAR POR NÚMERO DE CONTROL =======================
    elif menu == "🔍 Buscar por Número de Control":
        st.subheader("🔍 Buscar estudiantes por Número de Control")
        busqueda_num = st.text_input("Escribe el número de control:")

        if busqueda_num:
            # Normalizar el número de control
            num_input = re.sub(r'\D', '', busqueda_num.strip())
            num_normalizado = int(num_input) if num_input.isdigit() else num_input

            resultados = []
            for carrera in carreras:
                coleccion = db[carrera]

                # Consulta flexible
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

    # ======================= 3. VER ALUMNOS POR CARRERA =======================
    elif menu == "📖 Ver Alumnos por Carrera":
        st.subheader("📖 Ver Alumnos por Carrera")
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
                        st.dataframe(df_periodo[["NOMBRE_COMPLETO", "NUM.CONTROL"]])
                        seleccion = st.selectbox("Selecciona un estudiante:", df_periodo["NOMBRE_COMPLETO"].tolist())
                        if seleccion:
                            fila = df_periodo[df_periodo["NOMBRE_COMPLETO"] == seleccion].iloc[0]
                            st.json(fila.to_dict())
