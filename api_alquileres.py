from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pydantic import BaseModel
import pandas as pd
import numpy as np
from typing import Optional

app = FastAPI()



class Alquiler(BaseModel):
    latitud: float | None
    longitud: float | None
    place_l2: str
    place_l3: str
    operation: str
    property_type: str
    property_rooms: int | None
    property_bedrooms: int | None
    property_surface_total: float | None
    property_surface_covered: float | None
    property_price: float
    property_currency: str
    property_title: str
    id_localidad: Optional[int] = None

# Habilitar CORS para todos los orígenes (solo para desarrollo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite cualquier origen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_connection():
    return sqlite3.connect("mi_base.sqlite")

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

@app.post("/alquileres/")
def crear_alquiler(alquiler: Alquiler):
    conn = get_connection()
    cursor = conn.cursor()

    # Buscar id_localidad con place_l2 y place_l3
    cursor.execute("""
        SELECT id_localidad FROM localidades
        WHERE nombre = ? AND provincia = ?
        LIMIT 1
    """, (alquiler.place_l3, alquiler.place_l2))
    row = cursor.fetchone()
    id_localidad = row[0] if row else None

    # Insertar en alquileres usando el id_localidad encontrado o NULL si no existe
    cursor.execute("""
        INSERT INTO alquileres (
            latitud, longitud, place_l2, place_l3,
            operation, property_type, property_rooms,
            property_bedrooms, property_surface_total,
            property_surface_covered, property_price,
            property_currency, property_title, id_localidad
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        alquiler.latitud,
        alquiler.longitud,
        alquiler.place_l2,
        alquiler.place_l3,
        alquiler.operation,
        alquiler.property_type,
        alquiler.property_rooms,
        alquiler.property_bedrooms,
        alquiler.property_surface_total,
        alquiler.property_surface_covered,
        alquiler.property_price,
        alquiler.property_currency,
        alquiler.property_title,
        id_localidad
    ))

    conn.commit()
    conn.close()
    return {"mensaje": "Alquiler creado exitosamente"}