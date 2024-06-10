from kivymd.uix.screen import MDScreen
from kivymd.toast import toast
from kivy.properties import StringProperty
from kivy.clock import Clock
import threading
from kivymd.app import MDApp
from database.db_manager import DBManager
from kivymd.uix.relativelayout import MDRelativeLayout

class LoginScreen(MDScreen):
    username = StringProperty()
    password = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = DBManager()

    def on_enter(self):
        """Set focus on the username field when the screen is entered."""
        Clock.schedule_once(lambda dt: setattr(self.ids.input_username, 'focus', True), 0.5)

    def connect(self):
        """Handle login button press."""
        self.username = self.ids.input_username.text.strip()
        self.password = self.ids.input_password.text.strip()

        if self.validate_inputs(self.username, self.password):
            if DBManager._pool_ready.is_set():
                self.perform_login()
            else:
                self.show_toast("Inicializando conexiones... Inténtelo de nuevo.")
        else:
            self.show_toast("Usuario y/o contraseña no pueden estar vacíos.")

    def validate_inputs(self, username, password):
        """Validate user inputs."""
        return bool(username) and bool(password)

    def perform_login(self):
        """Perform the login action in a separate thread."""
        self.show_loading()
        threading.Thread(target=self._authenticate_user).start()

    def _authenticate_user(self):
        """Authenticate user with the database."""
        user_exists = self.db_manager.authenticate_user(self.username, self.password)
        Clock.schedule_once(lambda dt: self.on_authentication_result(user_exists), 0)

    def on_authentication_result(self, user_exists):
        """Handle the result of the authentication."""
        self.hide_loading()
        if user_exists:
            self.on_login_success()
        else:
            self.show_toast("Credenciales incorrectas. Inténtelo de nuevo.")
            self.ids.input_password.text = ""

    def on_login_success(self):
        """Handle successful login."""
        app = MDApp.get_running_app()
        self.db_manager.update_last_login(self.username)
        app.nav_controller.go_to_screen('home', 'left')

    def show_toast(self, message):
        """Show a toast with the given message."""
        toast(message)

    def show_loading(self):
        """Show loading spinner."""
        self.ids.spinner.active = True

    def hide_loading(self):
        """Hide loading spinner."""
        self.ids.spinner.active = False

class ClickableTextFieldRound(MDRelativeLayout):
    text = StringProperty()
    hint_text = StringProperty()
