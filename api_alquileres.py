from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import pandas as pd
import numpy as np

app = FastAPI()

# Habilitar CORS para todos los orígenes (solo para desarrollo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite cualquier origen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_connection():
    return sqlite3.connect("/home/milton/Desktop/Bases de datos/TP-BDD-1C2025/mi_base.sqlite")

@app.get("/alquileres/")
def buscar_alquileres(
    localidad: str = Query(None),
    provincia: str = Query(None),
    precio_min: float = Query(None),
    precio_max: float = Query(None),
    limit: int = Query(100)  # Limita a 100 resultados por defecto
):
    conn = get_connection()
    query = """
    SELECT a.*, l.nombre as localidad, l.provincia
    FROM alquileres a
    JOIN localidades l ON a.id_localidad = l.id_localidad
    WHERE 1=1
    """
    params = []
    if localidad:
        query += " AND l.nombre = ?"
        params.append(localidad)
    if provincia:
        query += " AND l.provincia = ?"
        params.append(provincia)
    if precio_min is not None:
        query += " AND a.property_price >= ?"
        params.append(precio_min)
    if precio_max is not None:
        query += " AND a.property_price <= ?"
        params.append(precio_max)
    query += " LIMIT ?"
    params.append(limit)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    df = df.replace({np.nan: None, np.inf: None, -np.inf: None})
    return df.to_dict(orient="records")

@app.get("/provincias/")
def listar_provincias():
    conn = get_connection()
    provincias = pd.read_sql("SELECT DISTINCT provincia FROM localidades ORDER BY provincia", conn)
    conn.close()
    return provincias['provincia'].dropna().tolist()

@app.get("/localidades/")
def listar_localidades(provincia: str = Query(None)):
    conn = get_connection()
    if provincia:
        localidades = pd.read_sql(
            "SELECT DISTINCT nombre FROM localidades WHERE provincia = ? ORDER BY nombre",
            conn, params=[provincia]
        )
    else:
        localidades = pd.read_sql(
            "SELECT DISTINCT nombre FROM localidades ORDER BY nombre",
            conn
        )
    conn.close()
    return localidades['nombre'].dropna().tolist()