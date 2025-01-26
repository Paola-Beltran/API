from fastapi import FastAPI, status, Depends, HTTPException
from sqlmodel import SQLModel, Field, Session, create_engine
from datetime import datetime # Se usa para trabajar con fechas y horas
from typing import Annotated # Indica dependencias
from contextlib import asynccontextmanager # Creacion de tablas en la base de datos

#crear conexion con la base datos
sqlite_nombre ="Paola.db" # nombre base de datos
sqlite_url = f"sqlite:///C:\\Paola\\API\\curso-fastapi-project\\{sqlite_nombre}" # ruta de acceso
motor = create_engine(sqlite_url) # conexion con la base de datos SQLite

# crear las tablas
@asynccontextmanager
async def create_all_tables(app: FastAPI): # etiqueta requerida que se ejecuta al iniciar la aplicacion y crea las tablas definidas en el modelo
    SQLModel.metadata.create_all(motor)
    yield


# Definir la aplicacion FastAPI
app = FastAPI(lifespan=create_all_tables) 


# abrir y cerrar una sesion de base de datos para cada solicitud
def get_session():
    with Session(motor) as sesion:
        yield sesion


# tipado y dependencias de FastAPI
sesionDep = Annotated[Session, Depends(get_session)]


# Se define el modelo de base de datos
class peliculasBase(SQLModel):
    Autor: str = Field()
    Descripcion: str = Field()
    Fecha_Estreno: datetime = Field()

# crear la tabla, que hereda la informacion del modelo
class peliculas(peliculasBase, table=True):
   id: int | None = Field(default=None, primary_key=True)

# hereda del modelo, para crear
class peliculas_creadas(peliculasBase):
    pass

# hereda del modelo, para actualizar
class peliculas_actualizadas(peliculasBase):
    pass

# crear una pelicula con el metodo post
@app.post("/peliculas",
          response_model = peliculas,
          status_code = status.HTTP_201_CREATED,
          tags=["peliculas"])
async def crear_peliculas(peliculas_data: peliculas_creadas, sesion: sesionDep):
    pelicula = peliculas.model_validate(peliculas_data.model_dump())
    sesion.add(pelicula)
    sesion.commit()
    sesion.refresh(pelicula)
    return pelicula


# leer una pelicula con el metodo get
@app.get("/peliculas/{_id}",
         response_model= peliculas,
         tags=["peliculas"])
async def leer_peliculas(peliculas_id: int, sesion: sesionDep):
    peliculas_db = sesion.get(peliculas, peliculas_id)
    if not peliculas_db:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail = "La pelicula no existe")
    return peliculas_db


# actualizar una pelicula con el metodo put
@app.put("/peliculas/{_id}",
           response_model= peliculas,
           status_code= status.HTTP_201_CREATED,
           tags=["peliculas"])
async def ajuste_pelicula(peliculas_id: int, peliculas_data: peliculas_actualizadas, sesion: sesionDep):
    peliculas_db = sesion.get(peliculas, peliculas_id)
    if not peliculas_db:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail = "La pelicula no existe")
    peliculas_data_dict = peliculas_data.model_dump(exclude_unset=True)
    peliculas_db.sqlmodel_update(peliculas_data_dict)
    sesion.add(peliculas_db)
    sesion.commit()
    sesion.refresh(peliculas_db)
    return peliculas_db


# eliminar una pelicula con el metodo delete
@app.delete("/peliculas/{_id}", tags=["peliculas"])
async def borrar_peliculas(peliculas_id: int, sesion: sesionDep):
    peliculas_db = sesion.get(peliculas, peliculas_id)
    if not peliculas_db:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= "La pelicula no existe")
    sesion.delete(peliculas_db)
    sesion.commit()
    return {"borrado": "Ok"}