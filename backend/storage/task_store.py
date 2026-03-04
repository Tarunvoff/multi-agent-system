tasks = {}

def save_task(task):
    tasks[task.id] = task

def get_task(task_id):
    return tasks.get(task_id)