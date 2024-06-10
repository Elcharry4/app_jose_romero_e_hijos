from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivy.clock import Clock
import os
from screens.login_screen import LoginScreen
from screens.home_screen import Home
from screens.empleados_screen import Empleados
from screens.config_screen import ConfigScreen
from screens.orders_screen import OrdersScreen
from screens.employee_details_screen import EmployeeDetailsScreen
from screens.activity_selection_screen import ActivitySelectionScreen
from screens.fundido_screen import FundidoScreen
from screens.history_screen import HistoryScreen
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from database.db_manager import DBManager
import threading

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
    def on_enter(self):
        threading.Thread(target=DBManager.initialize_pool, daemon=True).start()
        Clock.schedule_once(self.switch_to_login, 5)

    def switch_to_login(self, *args):
        app = MDApp.get_running_app()
        app.nav_controller.go_to_screen('login')

class MyApp(MDApp):
    def build(self):
        self.theme_cls.theme_style_switch_animation = True
        self.theme_cls.theme_style = 'Dark'

        # Obtener el directorio actual
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        resource_add_path(self.current_dir)
        LabelBase.register(name='Poppins', fn_regular=os.path.join(self.current_dir, 'sources', 'Poppins-SemiBold.ttf'))

        # Cargar el archivo .kv principal
        Builder.load_file(os.path.join(self.current_dir, 'kivy_files', 'pre_splash_screen.kv'))
        Builder.load_file(os.path.join(self.current_dir, 'kivy_files', 'login_screen.kv'))

        self.manager = ScreenManager(transition=SlideTransition(direction='left'))
        self.nav_controller = NavigationController(self.manager)
        self.manager.add_widget(SplashScreen(name='pre-splash'))
        self.manager.add_widget(LoginScreen(name='login'))

        return self.manager

    def on_start(self):
        Clock.schedule_once(self.go_to_splash, 0)
        Clock.schedule_once(self.load_other_screens, 0.1)

    def load_other_screens(self, dt):
        Builder.load_file(os.path.join(self.current_dir, 'kivy_files', 'home_screen.kv'))
        Builder.load_file(os.path.join(self.current_dir, 'kivy_files', 'config_screen.kv'))
        Builder.load_file(os.path.join(self.current_dir, 'kivy_files', 'empleados_screen.kv'))
        Builder.load_file(os.path.join(self.current_dir, 'kivy_files', 'orders_screen.kv'))
        Builder.load_file(os.path.join(self.current_dir, 'kivy_files', 'employee_details_screen.kv'))
        Builder.load_file(os.path.join(self.current_dir, 'kivy_files', 'activity_selection_screen.kv'))
        Builder.load_file(os.path.join(self.current_dir, 'kivy_files', 'fundido_screen.kv'))
        Builder.load_file(os.path.join(self.current_dir, 'kivy_files', 'history_screen.kv'))

        self.manager.add_widget(Home(name='home'))
        self.manager.add_widget(ConfigScreen(name='config'))
        self.manager.add_widget(Empleados(name='empleados'))
        self.manager.add_widget(OrdersScreen(name='orders'))
        self.manager.add_widget(EmployeeDetailsScreen(name='employee_details'))
        self.manager.add_widget(ActivitySelectionScreen(name='activity_selection'))
        self.manager.add_widget(FundidoScreen(name='fundido'))
        self.manager.add_widget(HistoryScreen(name='history'))

    def go_to_splash(self, *args):
        self.manager.current = 'pre-splash'
    
    def get_image_path(self, filename):
        return os.path.join(self.current_dir, 'sources', filename)

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