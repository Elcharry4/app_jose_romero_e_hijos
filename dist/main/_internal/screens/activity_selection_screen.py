from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivy.properties import StringProperty
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivy.clock import Clock, mainthread
from kivy.lang import Builder
import threading
from database.db_manager import DBManager
from kivymd.uix.textfield import MDTextField

class ActivitySelectionScreen(MDScreen):
    selected_activity_type = StringProperty("Moldeador")
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.employee_name = ""
        self.employee_id = None
        self.db_manager = DBManager()
        self.activities = []
        self.menu = None
        self.dialog = None
        self.task = None
        self.quantity_dialog = None
        self.setup_menu()

    def on_enter(self):
        self.load_activities()

    def setup_menu(self):
        menu_items = [
            {"text": "Moldeador", "viewclass": "OneLineListItem", "on_release": lambda: self.set_activity_type("Moldeador")},
            {"text": "General", "viewclass": "OneLineListItem", "on_release": lambda: self.set_activity_type("General")},
            {"text": "Fundidor", "viewclass": "OneLineListItem", "on_release": lambda: self.set_activity_type("Fundidor")},
        ]
        self.menu = MDDropdownMenu(
            caller=self.ids.activity_type_selector,
            items=menu_items,
            width_mult=4,
        )

    def set_employee(self, employee_id, employee_name):
        self.employee_id = employee_id
        self.employee_name = employee_name
        self.ids.toolbar.title = f"Seleccionar actividad para {employee_name}"

    def set_task(self, task):
        self.task = task

    def load_activities(self):
        self.show_loading()
        threading.Thread(target=self._load_activities).start()

    def _load_activities(self):
        self.activities = self.db_manager.get_activities_by_type(self.selected_activity_type)
        Clock.schedule_once(lambda dt: self.display_activities(), 0)
        Clock.schedule_once(lambda dt: self.hide_loading(), 0)

    @mainthread
    def display_activities(self):
        self.ids.rv.data = [{'text': activity, 'on_release': lambda x=activity: self.select_activity(x)} for activity in self.activities]

    def filter_activities(self, text):
        text = text.lower()
        filtered_activities = [activity for activity in self.activities if text in activity.lower()]
        self.ids.rv.data = [{'text': activity} for activity in filtered_activities]

    def select_activity(self, activity_name):
        if self.selected_activity_type == "Moldeador":
            self.show_quantity_dialog(activity_name)
        else:
            self.add_task(activity_name, 1)  # Default quantity for non-Moldeador activities

    def show_quantity_dialog(self, activity_name):
        self.quantity_dialog = MDDialog(
        title="Ingrese la cantidad de piezas",
        type="custom",
        content_cls=MDTextField(hint_text="Cantidad", input_filter="int", id="quantity_field"),
        buttons=[
            MDFlatButton(text="Cancelar", on_release=self.close_quantity_dialog),
            MDRaisedButton(text="Confirmar", on_release=lambda x: self.confirm_quantity(activity_name))
            ],
        )
        self.quantity_dialog.open()

    def close_quantity_dialog(self, *args):
        if self.quantity_dialog:
            self.quantity_dialog.dismiss()

    def confirm_quantity(self, activity_name):
        quantity_field = self.quantity_dialog.content_cls
        quantity = int(quantity_field.text) if quantity_field.text.isdigit() else 1
        self.close_quantity_dialog()
        self.add_task(activity_name, quantity)

    def add_task(self, activity_name, quantity):
        app = MDApp.get_running_app()
        employee_details_screen = app.manager.get_screen('employee_details')
        employee_details_screen.add_task(self.employee_id, activity_name, self.selected_activity_type, quantity)
        app.nav_controller.go_to_screen('employee_details', 'right')

    def show_loading(self):
        self.ids.spinner.active = True

    def hide_loading(self):
        self.ids.spinner.active = False

    def open_menu(self):
        self.menu.open()

    def set_activity_type(self, activity_type):
        self.selected_activity_type = activity_type
        self.ids.activity_type_selector.text = activity_type
        self.menu.dismiss()
        self.load_activities()
        if activity_type in ["General", "Fundidor"]:
            self.ids.add_task_button.opacity = 1
            self.ids.add_task_button.disabled = False
        else:
            self.ids.add_task_button.opacity = 0
            self.ids.add_task_button.disabled = True

    def show_add_task_dialog(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title="Agregar tarea",
                type="custom",
                content_cls=Builder.load_string("""
BoxLayout:
    orientation: 'vertical'
    spacing: dp(10)
    size_hint_y: None
    height: dp(120)
    MDTextField:
        id: task_name
        hint_text: "Nombre de la tarea"
    BoxLayout:
        size_hint_y: None
        height: dp(50)
        spacing: dp(10)
        MDRaisedButton:
            text: "Agregar"
            on_release: app.root.current_screen.add_task_dialog(task_name.text)
        MDFlatButton:
            text: "Cancelar"
            on_release: app.root.current_screen.dialog.dismiss()
"""),
            )
        self.dialog.open()

    def add_task_dialog(self, task_name):
        if task_name:
            threading.Thread(target=self._add_task_dialog, args=(task_name,)).start()
            self.dialog.dismiss()

    def _add_task_dialog(self, task_name):
        if self.selected_activity_type == "Fundidor":
            table_column = "fundidor"
        elif self.selected_activity_type == "General":
            table_column = "general"

        self.db_manager.add_activity(task_name, table_column)
        self.load_activities()
