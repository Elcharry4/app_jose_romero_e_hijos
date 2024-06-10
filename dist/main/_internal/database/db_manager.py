import mysql.connector.pooling
from configparser import ConfigParser
from models.task import Task
from models.employee_activity import EmployeeActivity
import os
from datetime import datetime
import threading

class DBManager:
    _instance = None
    _pool = None
    _pool_ready = threading.Event()  # Evento para indicar que el pool está listo

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DBManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        # No iniciar el pool aquí para evitar problemas de threading
        pass

    @classmethod
    def initialize_pool(cls):
        if not cls._pool:  # Crear el pool si no está creado
            cls._create_pool()

    @classmethod
    def _create_pool(cls):
        config = ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
        config.read(config_path)
        dbconfig = {
            'host': config.get('mysql', 'host'),
            'user': config.get('mysql', 'user'),
            'password': config.get('mysql', 'password'),
            'database': config.get('mysql', 'db'),
            'pool_size': 5,  # Ajusta el tamaño del pool según tus necesidades
            'pool_reset_session': True
        }
        try:
            cls._pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="mypool",
                **dbconfig
            )
            cls._pool_ready.set()  # Indicar que el pool está listo
        except Exception as e:
            print(f"Error al crear el pool de conexiones: {e}")
            cls._pool_ready.clear()  # Indicar que el pool no está listo

    def get_connection(self):
        if not self.__class__._pool_ready.is_set():
            raise Exception("Database connection pool is not initialized yet.")
        return self.__class__._pool.get_connection()

    def execute_query(self, query, params=None, fetchall=True, commit=False):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            if commit:
                conn.commit()
            if fetchall:
                result = cursor.fetchall()
                return result
            else:
                return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def execute_commit(self, query, params=None):
        self.execute_query(query, params, fetchall=False, commit=True)

    def add_employee(self, employee):
        query = "INSERT INTO empleados (nombre, apellido, seccion) VALUES (%s, %s, %s)"
        self.execute_commit(query, (employee.nombre, employee.apellido, employee.seccion))

    def add_task(self, employee_id, task):
        query = """
            INSERT INTO actividades_empleados (employee_id, nombre, tipo_actividad, cantidad, hora_inicio, hora_fin, prioridad)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        next_priority = self.get_next_priority(employee_id)
        params = (employee_id, task.name, task.activity_type, task.quantity, task.start_time, task.end_time, next_priority)
        self.execute_commit(query, params)
        task.task_id = self.get_last_insert_id()
        return task

    def get_last_insert_id(self):
        query = "SELECT LAST_INSERT_ID()"
        return self.execute_query(query, fetchall=False)[0]

    def get_employees(self):
        query = """
            SELECT e.id, e.nombre, e.apellido, ae.nombre, ae.cantidad, ae.hora_inicio 
            FROM empleados e
            LEFT JOIN (
                SELECT employee_id, nombre, cantidad, hora_inicio
                FROM actividades_empleados
                WHERE prioridad = 1
            ) ae ON e.id = ae.employee_id
            ORDER BY e.nombre, e.apellido
        """
        return [EmployeeActivity(*row) for row in self.execute_query(query)]

    def get_tasks_for_employee(self, employee_id):
        query = "SELECT * FROM actividades_empleados WHERE employee_id = %s ORDER BY prioridad"
        return [Task(row[0], row[2], row[3], row[4], row[5], row[6], row[7]) for row in self.execute_query(query, (employee_id,))]

    def update_task_start_time(self, task_id, start_time):
        query = "UPDATE actividades_empleados SET hora_inicio = %s WHERE id = %s"
        self.execute_commit(query, (start_time, task_id))

    def update_task_end_time(self, task_id, end_time):
        query = "UPDATE actividades_empleados SET hora_fin = %s WHERE id = %s"
        self.execute_commit(query, (end_time, task_id))

    def delete_task(self, task_id):
        query = "DELETE FROM actividades_empleados WHERE id = %s"
        self.execute_commit(query, (task_id,))

    def get_next_priority(self, employee_id):
        query = "SELECT IFNULL(MAX(prioridad), 0) + 1 FROM actividades_empleados WHERE employee_id = %s"
        return self.execute_query(query, (employee_id,), fetchall=False)[0]

    def update_task_priority(self, task_id, priority):
        query = "UPDATE actividades_empleados SET prioridad = %s WHERE id = %s"
        self.execute_commit(query, (priority, task_id))

    def swap_task_priorities(self, task1_id, task2_id):
        task1_priority = self.get_task_priority(task1_id)
        task2_priority = self.get_task_priority(task2_id)
        self.update_task_priority(task1_id, task2_priority)
        self.update_task_priority(task2_id, task1_priority)

    def get_task_priority(self, task_id):
        query = "SELECT prioridad FROM actividades_empleados WHERE id = %s"
        return self.execute_query(query, (task_id,), fetchall=False)[0]

    def decrement_priorities(self, employee_id, start_priority):
        query = """
            UPDATE actividades_empleados
            SET prioridad = prioridad - 1
            WHERE employee_id = %s AND prioridad > %s
        """
        self.execute_commit(query, (employee_id, start_priority))

    def get_activities_by_type(self, activity_type):
        if activity_type == "Moldeador":
            query = "SELECT IFNULL(NombrePieza, 'N/A') FROM piezas"
        elif activity_type == "Fundidor":
            query = "SELECT IFNULL(fundidor, 'N/A') FROM actividades WHERE fundidor IS NOT NULL"
        elif activity_type == "General":
            query = "SELECT IFNULL(general, 'N/A') FROM actividades WHERE general IS NOT NULL"
        return [row[0] for row in self.execute_query(query)]

    def add_activity(self, activity_name, table_column):
        query = f"INSERT INTO actividades ({table_column}) VALUES (%s)"
        self.execute_commit(query, (activity_name,))

    def complete_task(self, task_id, employee_id, real_quantity):
        query = """
            INSERT INTO actividades_empleados_finalizadas (employee_id, nombre, tipo_actividad, cantidad, hora_inicio, hora_fin, tiempo_fundido, tiempo_total)
            SELECT 
                employee_id, 
                nombre, 
                tipo_actividad, 
                %s,  -- Usar la cantidad real proporcionada
                hora_inicio, 
                hora_fin, 
                tiempo_fundido,
                SEC_TO_TIME(
                    TIMESTAMPDIFF(SECOND, hora_inicio, hora_fin) - (tiempo_fundido * 60)
                )
            FROM actividades_empleados
            WHERE id = %s
        """
        self.execute_commit(query, (real_quantity, task_id))
        self.delete_task(task_id)
        self.decrement_priorities(employee_id, 1)
        next_task_id = self.get_next_task_id(employee_id)
        if next_task_id:
            self.update_task_start_time(next_task_id, datetime.now())

    def get_next_task_id(self, employee_id):
        query = """
            SELECT id FROM actividades_empleados
            WHERE employee_id = %s AND prioridad = 1
        """
        result = self.execute_query(query, (employee_id,), fetchall=False)
        return result[0] if result else None

    def update_fundido_time(self, employee_id, minutes):
        query = """
            UPDATE actividades_empleados
            SET tiempo_fundido = tiempo_fundido + %s
            WHERE employee_id = %s AND prioridad = 1
        """
        self.execute_commit(query, (minutes, employee_id))

    def get_history_for_employee(self, employee_id):
        query = """
            SELECT 
                id, 
                nombre, 
                tipo_actividad, 
                cantidad, 
                hora_inicio, 
                hora_fin, 
                tiempo_total
            FROM actividades_empleados_finalizadas
            WHERE employee_id = %s
            ORDER BY hora_inicio DESC
        """
        return [Task(
            task_id=row[0],
            name=row[1],
            activity_type=row[2],
            quantity=row[3],
            start_time=row[4],
            end_time=row[5],
            priority=None,
            total_time=row[6]
        ) for row in self.execute_query(query, (employee_id,))]

    def authenticate_user(self, username, password):
        query = "SELECT 1 FROM users WHERE user = %s AND password = %s"
        return self.execute_query(query, (username, password), fetchall=False) is not None

    def update_last_login(self, username):
        query = "UPDATE users SET last_login = NOW() WHERE user = %s"
        self.execute_commit(query, (username,))

    def fech_employees(self):
        query = """
            SELECT id, nombre, apellido, seccion
            FROM empleados
        """
        return self.execute_query(query)

    def add_employee(self, name, lastname, section):
        query = "INSERT INTO empleados (nombre, apellido, seccion) VALUES (%s, %s, %s)"
        self.execute_commit(query, (name, lastname, section))

    def delete_employee(self, employee_id):
        query = "DELETE FROM empleados WHERE id = %s"
        self.execute_commit(query, (employee_id,))