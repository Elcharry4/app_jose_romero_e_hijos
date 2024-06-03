class Task:
    def __init__(self, task_id, name, activity_type, quantity, start_time=None, end_time=None, priority=None):
        self.task_id = task_id
        self.name = name
        self.activity_type = activity_type
        self.quantity = quantity
        self.start_time = start_time
        self.end_time = end_time
        self.priority = priority
