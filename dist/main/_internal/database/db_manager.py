import mysql.connector
from configparser import ConfigParser
from models.employee import Employee
from models.task import Task
import os
from datetime import datetime
from models.employee_activity import EmployeeActivity

class DBManager:
    def __init__(self):
        self.connect_to_db()

    def connect_to_db(self):
        config = ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
        config.read(config_path)
        self.conn = mysql.connector.connect(
            host=config.get('mysql', 'host'),
            user=config.get('mysql', 'user'),
            password=config.get('mysql', 'password'),
            database=config.get('mysql', 'db')
        )
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def close_db_connection(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS empleados (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                apellido VARCHAR(100) NOT NULL,
                seccion VARCHAR(100) NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS actividades_empleados (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id INT,
                nombre VARCHAR(255) NOT NULL,
                tipo_actividad VARCHAR(100) NOT NULL,
                cantidad INT,
                hora_inicio DATETIME,
                hora_fin DATETIME,
                prioridad INT,
                FOREIGN KEY (employee_id) REFERENCES empleados(id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS actividades_empleados_finalizadas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id INT,
                nombre VARCHAR(255) NOT NULL,
                tipo_actividad VARCHAR(100) NOT NULL,
                cantidad INT,
                hora_inicio DATETIME,
                hora_fin DATETIME,
                FOREIGN KEY (employee_id) REFERENCES empleados(id)
            )
        """)
        self.conn.commit()

    def add_employee(self, employee):
        self.cursor.execute("INSERT INTO empleados (nombre, apellido, seccion) VALUES (%s, %s, %s)",
                            (employee.nombre, employee.apellido, employee.seccion))
        self.conn.commit()

    def add_task(self, employee_id, task):
        next_priority = self.get_next_priority(employee_id)
        self.cursor.execute("""
            INSERT INTO actividades_empleados (employee_id, nombre, tipo_actividad, cantidad, hora_inicio, hora_fin, prioridad)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (employee_id, task.name, task.activity_type, task.quantity, task.start_time, task.end_time, next_priority))
        task.task_id = self.cursor.lastrowid  # Get the inserted task ID
        self.conn.commit()
        return task

    def get_employees(self):
        try:
            self.close_db_connection()
            self.connect_to_db()
            self.cursor.execute("""
                SELECT e.id, e.nombre, e.apellido, ae.nombre, ae.cantidad, ae.hora_inicio 
                FROM empleados e
                LEFT JOIN (
                    SELECT employee_id, nombre, cantidad, hora_inicio
                    FROM actividades_empleados
                    WHERE prioridad = 1
                ) ae ON e.id = ae.employee_id
                ORDER BY e.nombre, e.apellido
            """)
            employees = []
            for row in self.cursor.fetchall():
                employees.append(EmployeeActivity(row[0], row[1], row[2], row[3], row[4], row[5]))  # Utilizar la clase EmployeeActivity
            return employees
        except mysql.connector.errors.OperationalError as e:
            if e.errno == 2013:  # Lost connection to MySQL server during query
                self.connect_to_db()  # Reconnect to the database
                return self.get_employees()  # Retry the query
            else:
                raise

    def get_tasks_for_employee(self, employee_id):
        self.cursor.execute("SELECT * FROM actividades_empleados WHERE employee_id = %s ORDER BY prioridad", (employee_id,))
        tasks = []
        for row in self.cursor.fetchall():
            tasks.append(Task(row[0], row[2], row[3], row[4], row[5], row[6], row[7]))
        return tasks

    def update_task_start_time(self, task_id, start_time):
        self.cursor.execute("UPDATE actividades_empleados SET hora_inicio = %s WHERE id = %s", (start_time, task_id))
        self.conn.commit()

    def update_task_end_time(self, task_id, end_time):
        self.cursor.execute("UPDATE actividades_empleados SET hora_fin = %s WHERE id = %s", (end_time, task_id))
        self.conn.commit()

    def delete_task(self, task_id):
        self.cursor.execute("DELETE FROM actividades_empleados WHERE id = %s", (task_id,))
        self.conn.commit()

    def get_next_priority(self, employee_id):
        self.cursor.execute("SELECT IFNULL(MAX(prioridad), 0) + 1 FROM actividades_empleados WHERE employee_id = %s", (employee_id,))
        return self.cursor.fetchone()[0]

    def update_task_priority(self, task_id, priority):
        self.cursor.execute("UPDATE actividades_empleados SET prioridad = %s WHERE id = %s", (priority, task_id))
        self.conn.commit()

    def swap_task_priorities(self, task1_id, task2_id):
        self.cursor.execute("SELECT prioridad FROM actividades_empleados WHERE id = %s", (task1_id,))
        task1_priority = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT prioridad FROM actividades_empleados WHERE id = %s", (task2_id,))
        task2_priority = self.cursor.fetchone()[0]

        self.update_task_priority(task1_id, task2_priority)
        self.update_task_priority(task2_id, task1_priority)

    def decrement_priorities(self, employee_id, start_priority):
        self.cursor.execute("""
            UPDATE actividades_empleados
            SET prioridad = prioridad - 1
            WHERE employee_id = %s AND prioridad > %s
        """, (employee_id, start_priority))
        self.conn.commit()

    def get_activities_by_type(self, activity_type):
        if activity_type == "Moldeador":
            query = "SELECT IFNULL(NombrePieza, 'N/A') FROM piezas"
        elif activity_type == "Fundidor":
            query = "SELECT IFNULL(fundidor, 'N/A') FROM actividades WHERE fundidor IS NOT NULL"
        elif activity_type == "General":
            query = "SELECT IFNULL(general, 'N/A') FROM actividades WHERE general IS NOT NULL"
        self.cursor.execute(query)
        return [row[0] for row in self.cursor.fetchall()]

    def add_activity(self, activity_name, table_column):
        query = f"INSERT INTO actividades ({table_column}) VALUES (%s)"
        self.cursor.execute(query, (activity_name,))
        self.conn.commit()

    def complete_task(self, task_id, employee_id):
        # Mover la tarea completada a la tabla de finalizadas
        self.cursor.execute("""
            INSERT INTO actividades_empleados_finalizadas (employee_id, nombre, tipo_actividad, cantidad, hora_inicio, hora_fin)
            SELECT employee_id, nombre, tipo_actividad, cantidad, hora_inicio, hora_fin
            FROM actividades_empleados
            WHERE id = %s
        """, (task_id,))
        self.conn.commit()

        # Borrar la tarea de la tabla actual
        self.cursor.execute("DELETE FROM actividades_empleados WHERE id = %s", (task_id,))
        self.conn.commit()

        # Decrementar las prioridades de las tareas restantes
        self.decrement_priorities(employee_id, 1)

        # Check if the next task (priority 2) should start and update its start time
        self.cursor.execute("""
            SELECT id FROM actividades_empleados
            WHERE employee_id = %s AND prioridad = 1
        """, (employee_id,))
        next_task = self.cursor.fetchone()
        if next_task:
            self.update_task_start_time(next_task[0], datetime.now())
