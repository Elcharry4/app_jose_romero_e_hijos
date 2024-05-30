from kivy.app import App
import configparser
from kivymd.toast import toast
from kivymd.uix.screen import MDScreen
from datetime import datetime
import mysql.connector
import os
import threading
from kivy.clock import Clock

class Login(MDScreen):
    def connect(self):
        threading.Thread(target=self._connect).start()

    def _connect(self):
        app = App.get_running_app()
        input_username = app.manager.get_screen('login').ids['input_username'].text
        input_password = app.manager.get_screen('login').ids['input_password'].text

        # Inicializa las variables de configuración con valores predeterminados o None
        host = user = password = dbname = None
        db = None

        try:
            config = configparser.ConfigParser()
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
            config.read(config_path)
            host = config['mysql']['host']
            user = config['mysql']['user']
            password = config['mysql']['password']
            dbname = config['mysql']['db']

        except KeyError as e:
            print(f"Error: La clave {e} no se encontró en el archivo de configuración.")
        except Exception as e:
            print(f"Error no esperado al leer la configuración: {e}")

        try:
            db = mysql.connector.connect(host=host, user=user, password=password, database=dbname)
            cursor = db.cursor()
            query = "SELECT count(*) FROM users WHERE user = %s AND password = %s"
            cursor.execute(query, (input_username, input_password))
            count = cursor.fetchone()[0]

            if count == 0:
                Clock.schedule_once(lambda dt: toast('Contraseña Incorrecta'))
            else:
                Clock.schedule_once(lambda dt: toast('Contraseña correcta'))
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                query = "UPDATE users SET last_login = %s WHERE user = %s"
                cursor.execute(query, (now, input_username))
                db.commit()
                Clock.schedule_once(self.login_exitoso)

        except mysql.connector.Error as err:
            print("Error en la base de datos: {}".format(err))
        finally:
            if db and db.is_connected():
                db.close()

    def login_exitoso(self, dt):
        self.manager.current = 'home'    
