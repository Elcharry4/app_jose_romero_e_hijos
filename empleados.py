from kivymd.uix.screen import MDScreen
from kivymd.uix.responsivelayout import MDResponsiveLayout
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.floatlayout import MDFloatLayout
import configparser
import mysql.connector
import os
import threading
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.properties import StringProperty

class EmployeeTable(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = DatabaseManager()
        self.loading_data = False
        self.layout = MDFloatLayout(size_hint=(1, 1))
        self.selected_rows = []
        self.table = self.init_table()
        self.layout.add_widget(self.table)
        self.add_widget(self.layout)
        self.current_dialog = None

    def init_table(self, data=[]):
        self.table = MDDataTable(
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            use_pagination=True,
            check=True,
            column_data=[
                ("ID", dp(30)),
                ("Nombre", dp(60)),
                ("Apellido", dp(60)),
                ("Seccion", dp(60))
            ],
            row_data=data
        )
        self.table.bind(on_check_press=self.on_check_press)
        return self.table

    def fetch_data(self):
        if not self.loading_data:
            self.loading_data = True
            threading.Thread(target=self._fetch_data).start()
        else:
            print("Actualización ya en curso.")

    def _fetch_data(self):
        try:
            result = self.db_manager.fetch_employees()
            Clock.schedule_once(lambda dt: self.update_table(result))
        except Exception as e:
            print(f"Error al recuperar datos: {e}")
            Clock.schedule_once(lambda dt: self.update_table([]))
        finally:
            self.loading_data = False

    def update_table(self, data):
        if data:
            formatted_data = [(str(row[0]), row[1], row[2], row[3]) for row in data]
            self.layout.clear_widgets()
            self.table = self.init_table(formatted_data)
            self.layout.add_widget(self.table)

    def on_check_press(self, instance_table, current_row):
        if current_row in self.selected_rows:
            self.selected_rows.remove(current_row)
        else:
            self.selected_rows.append(current_row)

    def show_add_employee_form(self):
        content = AddEmployeeForm()
        self.current_dialog = MDDialog(
            title="Añadir Empleado",
            type="custom",
            content_cls=content,
            size_hint=(0.9, 0.6),
            buttons=[
                MDFlatButton(
                    text="Cancelar",
                    on_release=lambda x: self.current_dialog.dismiss()
                )
            ]
        )
        self.current_dialog.open()

    def add_employee(self, name, lastname, position):
        if name and lastname and position:
            def on_confirm():
                threading.Thread(target=self.perform_add, args=(name, lastname, position)).start()
            self.show_dialog("Agregar Empleados", f"¿Estás seguro que deseas añadir a {name} {lastname}?", on_confirm)
        else:
            self.show_dialog("Error", "Te olvidaste de llenar algun casillero del formulario.")

    def delete_selected_employees(self):
        def on_confirm():
            threading.Thread(target=self.perform_delete, args=(employee_id,)).start()
        if self.selected_rows:
            employee_id = self.selected_rows[0][0]
            employee_name = self.selected_rows[0][1]
            employee_lastname = self.selected_rows[0][2]
            self.show_dialog("Confirmar Eliminación", f"Estas seguro que deseas eliminar a {employee_name} {employee_lastname}?", on_confirm)
        else:
            self.show_dialog("Error", "No se ha seleccionado ningún empleado.")

    def show_dialog(self, title, text, on_confirm=None):
        if self.current_dialog:  
            self.current_dialog.dismiss()
            self.current_dialog = None
        buttons = [MDFlatButton(text="Cancelar", on_release=lambda x: self.dismiss_current_dialog())]
        if on_confirm:
            confirm_button = MDFlatButton(text="Confirmar", on_release=lambda x: on_confirm())
            buttons.append(confirm_button)

        self.current_dialog = MDDialog(title=title, text=text, buttons=buttons)
        self.current_dialog.open()

    def perform_delete(self, employee_id):
        success = self.db_manager.delete_employee(employee_id)
        Clock.schedule_once(lambda dt: self.show_result(success, "Empleado eliminado correctamente."))

    def perform_add(self, name, lastname, position):
        success = self.db_manager.add_employee(name, lastname, position)
        Clock.schedule_once(lambda dt: self.show_result(success, "Empleado agregado correctamente."))

    def show_result(self, success, message):
        self.dismiss_current_dialog()  # Asegúrate de cerrar cualquier diálogo antes de mostrar el resultado
        dialog_text = message if success else "Operación fallida."
        self.current_dialog = MDDialog(
            title="Resultado",
            text=dialog_text,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda _: self.close_dialog_and_refresh()
                )
            ]
        )
        self.current_dialog.open()

    def close_dialog_and_refresh(self):
        self.dismiss_current_dialog()
        self.fetch_data()

    def dismiss_current_dialog(self):
        if self.current_dialog:
            self.current_dialog.dismiss()
            self.current_dialog = None

class AddEmployeeForm(MDFloatLayout):
    name = StringProperty()
    lastname = StringProperty()
    position = StringProperty()

class MobileEmpleado(MDScreen):
    pass

class TabletEmpleado(MDScreen):
    pass

class DesktopEmpleado(MDScreen):
    pass

class ResponsiveEmpleado(MDResponsiveLayout, MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.mobile_view = MobileEmpleado()
        self.tablet_view = TabletEmpleado()
        self.desktop_view = DesktopEmpleado()

class Empleados(MDScreen):
    pass

class DatabaseManager:
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

    def fetch_employees(self):
        connection = self.get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT id, nombre, apellido, seccion FROM empleados")
            return cursor.fetchall()
        finally:
            if connection:
                connection.close()

    def add_employee(self, name, lastname, section):
        connection = self.get_connection()
        try:
            cursor = connection.cursor()
            sql = "INSERT INTO empleados (nombre, apellido, seccion) VALUES (%s, %s, %s)"
            cursor.execute(sql, (name, lastname, section))
            connection.commit()
            return cursor.rowcount > 0
        except mysql.connector.Error as err:
            print("Error al agregar empleado:", err)
            return False
        finally:
            if connection:
                connection.close()

    def delete_employee(self, employee_id):
        connection = self.get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM empleados WHERE id = %s", (employee_id,))
            rows_affected = cursor.rowcount
            connection.commit()
            return rows_affected > 0
        except mysql.connector.Error as err:
            print("Error al eliminar empleado:", err)
            return False
        finally:
            if connection:
                connection.close()