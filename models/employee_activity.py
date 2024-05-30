class EmployeeActivity:
    def __init__(self, employee_id, nombre, apellido, actividad, cantidad, hora_inicio):
        self.employee_id = employee_id
        self.nombre = nombre
        self.apellido = apellido
        self.actividad = actividad
        self.cantidad = cantidad
        self.hora_inicio = hora_inicio

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.actividad} ({self.cantidad}) iniciado en {self.hora_inicio}"