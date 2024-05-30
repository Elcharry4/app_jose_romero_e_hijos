from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivy.clock import Clock
from kivymd.uix.relativelayout import MDRelativeLayout
from kivy.properties import StringProperty
from login import Login
from home import Home
from empleados import Empleados, DatabaseManager, EmployeeTable
from config import ConfigScreen
from screens.orders_screen import OrdersScreen
from screens.employee_details_screen import EmployeeDetailsScreen
from screens.activity_selection_screen import ActivitySelectionScreen
import os

class ClickableTextFieldRound(MDRelativeLayout):
    text = StringProperty()
    hint_text = StringProperty()

class NavigationController:
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.drawers = {}

    def set_drawer(self, drawer, drawer_id):
        self.drawers[drawer_id] = drawer

    def open_drawer(self, drawer_id):
        if drawer_id in self.drawers:
            drawer = self.drawers[drawer_id].ids.nav_drawer
            drawer.set_state("open")

    def go_to_screen(self, screen_name, direction='left'):
        self.screen_manager.transition = SlideTransition(direction=direction)
        self.screen_manager.current = screen_name

class SplashScreen(MDScreen):
    pass

class MyApp(MDApp):
    def build(self):
        self.theme_cls.theme_style_switch_animation = True
        self.theme_cls.theme_style = 'Dark'

        # Obtener el directorio actual
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Cargar archivos .kv con rutas relativas
        Builder.load_file(os.path.join(current_dir, 'pre-splash.kv'))
        Builder.load_file(os.path.join(current_dir, 'login.kv'))
        Builder.load_file(os.path.join(current_dir, 'home.kv'))
        Builder.load_file(os.path.join(current_dir, 'config.kv'))
        Builder.load_file(os.path.join(current_dir, 'empleados.kv'))
        Builder.load_file(os.path.join(current_dir, 'kivy_files', 'orders_screen.kv'))
        Builder.load_file(os.path.join(current_dir, 'kivy_files', 'employee_details_screen.kv'))
        Builder.load_file(os.path.join(current_dir, 'kivy_files', 'activity_selection_screen.kv'))

        self.manager = ScreenManager(transition=SlideTransition(direction='left'))
        self.nav_controller = NavigationController(self.manager)
        self.DatabaseManager = DatabaseManager()
        self.EmployeeTable = EmployeeTable()
        self.manager.add_widget(SplashScreen(name='pre-splash'))
        self.manager.add_widget(Login(name='login'))
        self.manager.add_widget(Home(name='home'))
        self.manager.add_widget(ConfigScreen(name='config'))
        self.manager.add_widget(Empleados(name='empleados'))
        self.manager.add_widget(OrdersScreen(name='orders'))
        self.manager.add_widget(EmployeeDetailsScreen(name='employee_details'))
        self.manager.add_widget(ActivitySelectionScreen(name='activity_selection'))
        return self.manager

    def on_start(self):
        Clock.schedule_once(self.login, 3)

    def login(self, *args):
        self.manager.current = 'login'

    def logout(self):
        self.manager.current = 'login'

    def switch_to_screen(self, screen_name):
        if screen_name in self.manager.screen_names:
            self.manager.current = screen_name

    def switch_theme_style(self):
        self.theme_cls.theme_style = (
            'Dark' if self.theme_cls.theme_style == 'Light' else 'Light'
        )

if __name__ == '__main__':
    MyApp().run()
