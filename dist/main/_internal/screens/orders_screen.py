from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.list import IconLeftWidget
from kivymd.app import MDApp
from database.db_manager import DBManager
from kivy.clock import Clock
import threading
import mysql.connector

class OrdersScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = DBManager()
        self.filtered_employees = []
        self.search_delay = None

    def on_enter(self):
        self.load_employees()

    def load_employees(self):
        self.show_loading()
        threading.Thread(target=self._load_employees).start()

    def _load_employees(self):
        try:
            employees = self.db_manager.get_employees()
            self.filtered_employees = employees
            Clock.schedule_once(lambda dt: self.display_employees(employees), 0)
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            Clock.schedule_once(lambda dt: self.hide_loading(), 0)

    def display_employees(self, employees):
        self.ids.employee_list_layout.clear_widgets()
        for employee in employees:
            item_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)

            # Añadir información del empleado
            item_layout.add_widget(MDLabel(text=f"{employee.nombre} {employee.apellido}", size_hint_x=0.25))

            # Añadir tarea, cantidad y hora de inicio, con comprobación para evitar errores de índice
            tarea = employee.actividad if employee.actividad else "N/A"
            cantidad = str(employee.cantidad) if employee.cantidad else "N/A"
            hora_inicio = employee.hora_inicio.strftime("%d/%m/%Y %H:%M:%S") if employee.hora_inicio else "N/A"

            item_layout.add_widget(MDLabel(text=tarea, size_hint_x=0.25))
            item_layout.add_widget(MDLabel(text=cantidad, size_hint_x=0.25))
            item_layout.add_widget(MDLabel(text=hora_inicio, size_hint_x=0.25))

            edit_icon = IconLeftWidget(icon="pencil", on_release=lambda x, emp_id=employee.employee_id, name=f"{employee.nombre} {employee.apellido}": self.edit_employee(emp_id, name))
            item_layout.add_widget(edit_icon)
            self.ids.employee_list_layout.add_widget(item_layout)

    def edit_employee(self, employee_id, employee_name):
        app = MDApp.get_running_app()
        app.manager.get_screen('employee_details').update_employee_id(employee_id, employee_name)
        app.nav_controller.go_to_screen('employee_details', direction='left')

    def on_search(self, text):
        if self.search_delay:
            self.search_delay.cancel()
        self.search_delay = Clock.schedule_once(lambda dt: self.filter_employees(text), 0.5)

    def filter_employees(self, text):
        filtered = [emp for emp in self.filtered_employees if text.lower() in f"{emp.nombre} {emp.apellido}".lower()]
        self.display_employees(filtered)

    def show_loading(self):
        self.ids.spinner.active = True

    def hide_loading(self):
        self.ids.spinner.active = False
