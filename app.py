# ======================= IMPORTS =======================
import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import date

# ======================= CONFIGURACIÓN =======================
st.set_page_config(page_title="Sistema de Estudiantes", page_icon="🎓", layout="wide")
st.markdown(
    """
    <style>
    .main {
        background-color: #1E1E1E;
        color: white;
    }
    .stButton>button {
        background-color: #4A90E2;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
    }
    .stButton>button:hover {
        background-color: #0066cc;
    }
    .stTextInput>div>div>input {
        color: black;
    }
    .stSelectbox>div>div>select {
        color: black;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ======================= USUARIOS =======================
USERS = {
    "admin": "1234",
    "misa": "CADAN09",
    "Mto.Toledo": "CADAN0218",
    "Sec.Veronica": "CADAN0114"
}

# ======================= SESIÓN =======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "carrera" not in st.session_state:
    st.session_state.carrera = ""
if "periodo" not in st.session_state:
    st.session_state.periodo = ""
if "guardados" not in st.session_state:
    st.session_state.guardados = pd.DataFrame(columns=[
        "NOMBRE_COMPLETO", "NUM.CONTROL", "PERIODO", "C", "A. INTERNO", "A. EXTERNO"
    ])

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
        st.session_state.carrera = ""
        st.session_state.periodo = ""
        st.session_state.guardados = pd.DataFrame(columns=[
            "NOMBRE_COMPLETO", "NUM.CONTROL", "PERIODO", "C", "A. INTERNO", "A. EXTERNO"
        ])
        st.rerun()

    st.sidebar.markdown("### Menú de Navegación")
    menu = st.sidebar.radio("Selecciona opción:", [
        "🔍 Buscar por Nombre o Número de Control",
        "📖 Ver Alumnos por Carrera",
        "📖 Ver / Editar estudiantes",
        "📤 Subir Archivo CSV"
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
        df_all_data = df_all_data.dropna(subset=["NOMBRE (S)", "NUM.CONTROL"])

        # Verificar que las columnas existen
        columns_to_check = ["NOMBRE (S)", "A. PAT", "A. MAT", "NUM.CONTROL"]
        for col in columns_to_check:
            if col not in df_all_data.columns:
                st.error(f"La columna '{col}' no existe en el DataFrame.")
                st.stop()

        # Buscador por nombre o número de control
        search_term = st.text_input("Buscar por Nombre o Número de Control", key="search_term")

        if search_term:
            df_filtered = df_all_data[
                df_all_data["NOMBRE (S)"].str.contains(search_term, case=False, na=False) |
                df_all_data["A. PAT"].str.contains(search_term, case=False, na=False) |
                df_all_data["A. MAT"].str.contains(search_term, case=False, na=False) |
                df_all_data["NUM.CONTROL"].astype(str).str.contains(search_term, case=False, na=False)
            ]
        else:
            df_filtered = df_all_data

        # Mostrar la primera tabla con los resultados filtrados
        st.dataframe(df_filtered[columns_to_check])

        # Seleccionar un estudiante de la primera tabla
        if not df_filtered.empty:
            estudiante = st.selectbox("Selecciona un estudiante:", df_filtered["NOMBRE (S)"].tolist())
            fila = df_filtered[df_filtered["NOMBRE (S)"] == estudiante].iloc[0]

            # Mostrar la segunda tabla con todos los datos del estudiante seleccionado
            st.subheader("Datos del Estudiante Seleccionado")
            st.dataframe(fila.to_frame().T)

            # Botón para guardar los datos del estudiante
            if st.button("Guardar"):
                datos_guardados = {
                    "NOMBRE_COMPLETO": fila.get("NOMBRE (S)", "") + " " + fila.get("A. PAT", "") + " " + fila.get("A. MAT", ""),
                    "NUM.CONTROL": fila.get("NUM.CONTROL", ""),
                    "PERIODO": fila.get("PERIODO", ""),
                    "C": st.session_state.carrera,  # Asegurar que se asigna la carrera correcta
                    "A. INTERNO": fila.get("A. INTERNO", ""),
                    "A. EXTERNO": fila.get("A. EXTERNO", "")
                }
                st.session_state.guardados = pd.concat([st.session_state.guardados, pd.DataFrame([datos_guardados])], ignore_index=True)
                st.success("✅ Datos guardados correctamente.")

            # Mostrar la tabla de estudiantes guardados
            st.subheader("Estudiantes Guardados")
            st.dataframe(st.session_state.guardados)

            # Botón para imprimir la tabla de estudiantes guardados
            if st.button("Imprimir Estudiantes Guardados"):
                st.write(st.session_state.guardados.to_csv(index=False))
                st.success("✅ Datos impresos correctamente.")

    # ======================= 2. VER ALUMNOS POR CARRERA =======================
    elif menu == "📖 Ver Alumnos por Carrera":
        st.subheader("📖 Ver Alumnos por Carrera")

        # Botones para seleccionar carrera
        col1, col2 = st.columns(2)
        if col1.button("Ingeniería en Informática (I.I)"):
            st.session_state.carrera = "I.I"
        elif col2.button("Ingeniería en Sistemas Computacionales (I.S.C)"):
            st.session_state.carrera = "I.S.C"

        if st.session_state.carrera:
            coleccion = db[st.session_state.carrera]
            periodos = coleccion.distinct("PERIODO")
            if periodos:
                st.session_state.periodo = st.selectbox("Selecciona periodo:", periodos)
                if st.session_state.periodo:
                    df_periodo = pd.DataFrame(list(coleccion.find({"PERIODO": st.session_state.periodo}, {"_id": 0})))

                    # Verificar que las columnas existan
                    required_columns = ["NOMBRE (S)", "NUM.CONTROL"]
                    for col in required_columns:
                        if col not in df_periodo.columns:
                            st.error(f"La columna '{col}' no existe en el DataFrame.")
                            st.stop()

                    # Filtrar registros sin nombre o número de control
                    df_periodo = df_periodo.dropna(subset=required_columns)

                    if not df_periodo.empty:
                        df_periodo["NOMBRE_COMPLETO"] = (
                            df_periodo.get("NOMBRE (S)", pd.Series([""]*len(df_periodo))).fillna("") + " " +
                            df_periodo.get("A. PAT", pd.Series([""]*len(df_periodo))).fillna("") + " " +
                            df_periodo.get("A. MAT", pd.Series([""]*len(df_periodo))).fillna("")
                        )

                        # Mostrar la tabla con nombre completo y número de control
                        st.dataframe(df_periodo[["NOMBRE_COMPLETO", "NUM.CONTROL"]])

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
                            num_control = st.text_input("Número de control", value=str(fila.get("NUM.CONTROL", "")))
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
                                    {"NUM.CONTROL": fila.get("NUM.CONTROL", ""), "PERIODO": periodo},
                                    {"$set": {
                                        "NOMBRE (S)": nombre,
                                        "A. PAT": apellido_pat,
                                        "A. MAT": apellido_mat,
                                        "NUM.CONTROL": int(num_control.strip()) if num_control.strip().isdigit() else num_control,
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

    # ======================= 4. SUBIR ARCHIVO CSV =======================
    elif menu == "📤 Subir Archivo CSV":
        st.subheader("📤 Subir Archivo CSV")

        # Widget para subir archivo
        uploaded_file = st.file_uploader("Elige un archivo CSV", type=["csv"])

        if uploaded_file is not None:
            # Leer el archivo CSV
            df_uploaded = pd.read_csv(uploaded_file, encoding="latin1")

            # Verificar que las columnas existen
            required_columns = ["NOMBRE (S)", "A. PAT", "A. MAT", "NUM.CONTROL", "PERIODO"]
            for col in required_columns:
                if col not in df_uploaded.columns:
                    st.error(f"La columna '{col}' no existe en el archivo CSV.")
                    st.stop()

            # Filtrar registros sin nombre o número de control
            df_uploaded = df_uploaded.dropna(subset=["NOMBRE (S)", "NUM.CONTROL"])

            # Mostrar el DataFrame cargado
            st.dataframe(df_uploaded)

            # Seleccionar carrera y periodo
            carrera = st.selectbox("Selecciona carrera:", carreras)
            if carrera:
                periodo = st.selectbox("Selecciona periodo:", df_uploaded["PERIODO"].unique())

                if st.button("Subir a MongoDB"):
                    coleccion = db[carrera]
                    data_dict = df_uploaded[df_uploaded["PERIODO"] == periodo].to_dict("records")

                    if data_dict:
                        coleccion.insert_many(data_dict)
                        st.success(f"✅ Se insertaron {len(data_dict)} registros en MongoDB correctamente.")
                    else:
                        st.error("❌ No se encontraron datos para insertar.")
