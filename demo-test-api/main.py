from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
from contextlib import contextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Demo Test API - Alumnos",
    servers=[
        {"url": "http://host.docker.internal:8020", "description": "Demo API Server"}
    ]
)

DATABASE = "alumnos.db"


class AlumnoCreate(BaseModel):
    nombre: str
    apellido: str
    edad: int
    email: str
    carrera: str


class Alumno(BaseModel):
    id: int
    nombre: str
    apellido: str
    edad: int
    email: str
    carrera: str


@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alumnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                edad INTEGER NOT NULL,
                email TEXT NOT NULL UNIQUE,
                carrera TEXT NOT NULL
            )
        """)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom handler for validation errors to provide better debugging."""
    body = await request.body()
    logger.error(f"Validation error for request to {request.url.path}")
    logger.error(f"Request body: {body.decode() if body else 'empty'}")
    logger.error(f"Validation errors: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": body.decode() if body else None},
    )


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
async def root():
    return {"message": "Demo Test API - Alumnos", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/alumnos", response_model=Alumno, status_code=201)
async def create_alumno(alumno: AlumnoCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO alumnos (nombre, apellido, edad, email, carrera)
                   VALUES (?, ?, ?, ?, ?)""",
                (alumno.nombre, alumno.apellido, alumno.edad, alumno.email, alumno.carrera)
            )
            alumno_id = cursor.lastrowid
            cursor.execute("SELECT * FROM alumnos WHERE id = ?", (alumno_id,))
            row = cursor.fetchone()
            return dict(row)
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Email ya existe")


@app.get("/alumnos", response_model=List[Alumno])
async def get_alumnos(skip: int = 0, limit: int = 100):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM alumnos LIMIT ? OFFSET ?", (limit, skip))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


@app.get("/alumnos/{alumno_id}", response_model=Alumno)
async def get_alumno(alumno_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM alumnos WHERE id = ?", (alumno_id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Alumno no encontrado")
        return dict(row)


@app.put("/alumnos/{alumno_id}", response_model=Alumno)
async def update_alumno(alumno_id: int, alumno: AlumnoCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM alumnos WHERE id = ?", (alumno_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Alumno no encontrado")

        try:
            cursor.execute(
                """UPDATE alumnos
                   SET nombre = ?, apellido = ?, edad = ?, email = ?, carrera = ?
                   WHERE id = ?""",
                (alumno.nombre, alumno.apellido, alumno.edad, alumno.email, alumno.carrera, alumno_id)
            )
            cursor.execute("SELECT * FROM alumnos WHERE id = ?", (alumno_id,))
            row = cursor.fetchone()
            return dict(row)
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Email ya existe")


@app.delete("/alumnos/{alumno_id}", status_code=204)
async def delete_alumno(alumno_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM alumnos WHERE id = ?", (alumno_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Alumno no encontrado")
        cursor.execute("DELETE FROM alumnos WHERE id = ?", (alumno_id,))
