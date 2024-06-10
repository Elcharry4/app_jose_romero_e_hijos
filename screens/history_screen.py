from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivy.properties import StringProperty
import threading
from kivy.clock import Clock
from database.db_manager import DBManager

class HistoryScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = DBManager()  # Alternativa: usar MDApp.get_running_app().db_manager
        self.employee_id = None
        self.employee_name = ""
        self.history_items = []

    def update_employee_id(self, employee_id, employee_name):
        self.employee_id = employee_id
        self.employee_name = employee_name
        self.ids.toolbar.title = f"Historial de {employee_name}"
        self.load_history()

    def load_history(self):
        self.show_loading()
        threading.Thread(target=self._load_history).start()

    def _load_history(self):
        self.history_items = self.db_manager.get_history_for_employee(self.employee_id)
        Clock.schedule_once(lambda dt: self.display_history(self.history_items), 0)
        Clock.schedule_once(lambda dt: self.hide_loading(), 0)

    def display_history(self, history_items):
        self.ids.history_list.clear_widgets()
        for item in history_items:
            self.ids.history_list.add_widget(HistoryItem(
                task_name=item.name,
                quantity=str(item.quantity),
                activity_type=item.activity_type,
                start_time=str(item.start_time),
                end_time=str(item.end_time),
                total_time=str(item.total_time)
            ))

    def filter_history(self, search_text):
        search_text = search_text.lower()
        filtered_items = [item for item in self.history_items if search_text in item.name.lower()]
        self.display_history(filtered_items)

    def show_loading(self):
        self.ids.spinner.active = True

    def hide_loading(self):
        self.ids.spinner.active = False

class HistoryItem(MDCard):
    task_name = StringProperty()
    quantity = StringProperty()
    activity_type = StringProperty()
    start_time = StringProperty()
    end_time = StringProperty()
    total_time = StringProperty()
