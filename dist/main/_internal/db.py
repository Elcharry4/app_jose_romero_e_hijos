import mysql.connector
import configparser
import os
from models import Empleado, Actividad

class Database:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
        self.config.read(self.config_path)

    def get_connection(self):
        return mysql.connector.connect(
            host=self.config['mysql']['host'],
            user=self.config['mysql']['user'],
            password=self.config['mysql']['password'],
            database=self.config['mysql']['db']
        )

    def obtener_empleados(self):
        conexion = self.get_connection()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, nombre, apellido, seccion FROM empleados")
        empleados = [Empleado(id, nombre, apellido, seccion) for id, nombre, apellido, seccion in cursor.fetchall()]
        conexion.close()
        return empleados

    def guardar_actividad(self, empleado_id, actividad):
        conexion = self.get_connection()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO actividades_empleados (empleado_id, actividad_actual, inicio, cantidad, tipo_actividad) VALUES (%s, %s, %s, %s, %s)",
            (empleado_id, actividad.nombre, actividad.inicio, actividad.cantidad, actividad.tipo)
        )
        conexion.commit()
        conexion.close()