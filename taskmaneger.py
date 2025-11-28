class Taskmanedger:
        def __init__(self):
            self.tasks = []  # Храним задачи в списке

        def createTask(self, name, desc):
            task = {"name": name, "description": desc}
            self.tasks.append(task)

        def get_tasks(self):
            return self.tasks  # Возвращаем реальный список задач
