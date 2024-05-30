from kivymd.uix.tab import MDTabsBase
from kivymd.uix.screen import MDScreen
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.responsivelayout import MDResponsiveLayout
from kivy.app import App
from kivy.uix.scrollview import ScrollView

class ButtonAdministracion(ScrollView):
    def on_button_press(self, button_text):
        app = App.get_running_app()
        if button_text == "Empleados":
            app.manager.current = 'empleados'

class ButtonProducion(ScrollView):
    def on_button_press(self, button_text):
        app = App.get_running_app()
        if button_text == "Ordenes":
            app.manager.current = 'orders'
class ButtonLaboratorio(ScrollView):
    pass
class ButtonOtros(ScrollView):
    pass

class Tab(MDFloatLayout, MDTabsBase):
    pass

class MobileHome(MDScreen):
    def on_tab_switch(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        pass

class TabletHome(MDScreen):
    def on_tab_switch(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        pass

class DesktopHome(MDScreen):
    def on_tab_switch(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        pass

class ResponsiveHome(MDResponsiveLayout, MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.mobile_view = MobileHome()
        self.tablet_view = TabletHome()
        self.desktop_view = DesktopHome()

class Home(MDScreen):
    pass