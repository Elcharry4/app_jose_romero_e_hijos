from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty, ObjectProperty
from kivy.clock import Clock
import threading
from database.db_manager import DBManager

class FundidoScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = DBManager()
        self.selected_employees = set()
        self.fundido_dialog = None

    def on_enter(self):
        self.load_employees()

    def load_employees(self):
        self.show_loading()
        threading.Thread(target=self._load_employees).start()

    def _load_employees(self):
        employees = self.db_manager.get_employees()
        Clock.schedule_once(lambda dt: self.display_employees(employees), 0)
        Clock.schedule_once(lambda dt: self.hide_loading(), 0)

    def display_employees(self, employees):
        self.ids.employee_grid.clear_widgets()
        self.selected_employees.clear()  # Clear previously selected employees
        for employee in employees:
            item = SelectableEmployeeItem(name=f"{employee.nombre} {employee.apellido}", employee_id=employee.employee_id)
            item.checkbox.bind(active=self.on_employee_selected)
            self.ids.employee_grid.add_widget(item)

    def on_employee_selected(self, checkbox, is_active):
        # Get the parent item that contains this checkbox
        parent_item = checkbox.parent
        if parent_item and isinstance(parent_item, SelectableEmployeeItem):
            employee_id = parent_item.employee_id
            if is_active:
                self.selected_employees.add(employee_id)
            else:
                self.selected_employees.discard(employee_id)

    def show_fundido_dialog(self):
        if not self.fundido_dialog:
            self.fundido_dialog = MDDialog(
                title="Ingrese el tiempo de fundición (minutos)",
                type="custom",
                content_cls=MDTextField(hint_text="Tiempo en minutos", input_filter="int", id="fundido_field"),
                buttons=[
                    MDFlatButton(text="Cancelar", on_release=lambda x: self.fundido_dialog.dismiss()),
                    MDRaisedButton(text="Guardar", on_release=lambda x: self.save_fundido_time())
                ],
            )
        self.fundido_dialog.open()

    def save_fundido_time(self):
        time_field = self.fundido_dialog.content_cls
        try:
            fundido_time = int(time_field.text)
        except ValueError:
            fundido_time = 0

        self.fundido_dialog.dismiss()

        threading.Thread(target=self._save_fundido_time, args=(fundido_time,)).start()

    def _save_fundido_time(self, fundido_time):
        for employee_id in self.selected_employees:
            self.db_manager.update_fundido_time(employee_id, fundido_time)
        self.load_employees()  # Recargar la lista después de guardar el tiempo

    def show_loading(self):
        self.ids.spinner.active = True

    def hide_loading(self):
        self.ids.spinner.active = False

class SelectableEmployeeItem(MDBoxLayout):
    name = StringProperty("")
    employee_id = ObjectProperty(None)
    checkbox = ObjectProperty(None)

    def __init__(self, name, employee_id, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.employee_id = employee_id
        self.checkbox = self.ids.checkbox

    def on_checkbox_active(self, checkbox, value):
        parent = self.parent
        if parent and hasattr(parent, 'on_employee_selected'):
            parent.on_employee_selected(checkbox, value)

    def on_kv_post(self, base_widget):
        self.checkbox = self.ids.checkbox

    def toggle_checkbox(self):
        if self.checkbox:
            self.checkbox.active = not self.checkbox.active

    def on_release(self):
        self.toggle_checkbox()

class ButtonLabel(ButtonBehavior, MDLabel):
    pass
