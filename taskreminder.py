import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from threading import Timer
from datetime import datetime
import pyttsx3
import json
import matplotlib.pyplot as plt

class TaskReminder:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Reminder Bot")
        self.tasks = []
        self.completed_tasks = {}
        self.reminder_timers = []

        self.frame = ttk.Frame(self.root, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Button(self.frame, text="Add Task", command=self.add_task).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(self.frame, text="Edit Task", command=self.edit_task).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.frame, text="Delete Task", command=self.delete_task).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(self.frame, text="Save Tasks", command=self.save_tasks).grid(row=0, column=3, padx=5, pady=5)
        ttk.Button(self.frame, text="Load Tasks", command=self.load_tasks).grid(row=0, column=4, padx=5, pady=5)
        
        self.task_listbox = tk.Listbox(self.frame, width=80, height=15)
        self.task_listbox.grid(row=1, column=0, columnspan=5, padx=5, pady=5)

        ttk.Button(self.frame, text="Set Reminder", command=self.schedule_reminders).grid(row=2, column=0, padx=5, pady=5)
        ttk.Button(self.frame, text="Stop Reminders", command=self.stop_reminders).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(self.frame, text="Consistency Graph", command=self.show_consistency_graph).grid(row=2, column=2, padx=5, pady=5)
        
        self.welcome_message()

    def welcome_message(self):
        if not self.tasks:
            message = "Welcome! There are no pending tasks today. Please add some tasks."
        else:
            message = "Welcome! You have pending tasks."
        self.speak_message(message)

    def add_task(self):
        task_name = simpledialog.askstring("Task", "Enter task name:")
        if task_name:
            due_date_str = simpledialog.askstring("Due Date", "Enter due date (DD/MM/YY HH:MM AM/PM):")
            try:
                due_date = datetime.strptime(due_date_str, "%d/%m/%y %I:%M %p")
            except ValueError:
                messagebox.showerror("Invalid Date", "Enter date in format (DD/MM/YY HH:MM AM/PM).")
                return
            priority = simpledialog.askstring("Priority", "Enter priority (High/Medium/Low):")
            self.tasks.append({'name': task_name, 'due_date': due_date, 'priority': priority})
            self.update_task_list()

    def edit_task(self):
        selected_task_index = self.task_listbox.curselection()
        if not selected_task_index:
            messagebox.showwarning("No Selection", "Please select a task to edit.")
            return
        task = self.tasks[selected_task_index[0]]
        task_name = simpledialog.askstring("Task", "Edit task name:", initialvalue=task['name'])
        if task_name:
            due_date_str = simpledialog.askstring("Due Date", "Edit due date (DD/MM/YY HH:MM AM/PM):", initialvalue=task['due_date'].strftime('%d/%m/%y %I:%M %p'))
            try:
                due_date = datetime.strptime(due_date_str, "%d/%m/%y %I:%M %p")
            except ValueError:
                messagebox.showerror("Invalid Date", "Enter date in format (DD/MM/YY HH:MM AM/PM).")
                return
            priority = simpledialog.askstring("Priority", "Edit priority (High/Medium/Low):", initialvalue=task['priority'])
            self.tasks[selected_task_index[0]] = {'name': task_name, 'due_date': due_date, 'priority': priority}
            self.update_task_list()

    def delete_task(self):
        selected_task_index = self.task_listbox.curselection()
        if not selected_task_index:
            messagebox.showwarning("No Selection", "Please select a task to delete.")
            return
        completed_task = self.tasks[selected_task_index[0]]
        date_str = completed_task['due_date'].strftime('%d/%m/%y')
        if date_str in self.completed_tasks:
            self.completed_tasks[date_str] += 1
        else:
            self.completed_tasks[date_str] = 1
        del self.tasks[selected_task_index[0]]
        self.update_task_list()

    def save_tasks(self):
        with open("tasks.json", "w") as file:
            tasks_to_save = [{'name': task['name'], 'due_date': task['due_date'].strftime('%d/%m/%y %I:%M %p'), 'priority': task['priority']} for task in self.tasks]
            json.dump({'tasks': tasks_to_save, 'completed_tasks': self.completed_tasks}, file)
        messagebox.showinfo("Save Tasks", "Tasks saved successfully.")

    def load_tasks(self):
        try:
            with open("tasks.json", "r") as file:
                data = json.load(file)
                tasks_to_load = data.get('tasks', [])
                self.completed_tasks = data.get('completed_tasks', {})
                self.tasks = [{'name': task['name'], 'due_date': datetime.strptime(task['due_date'], '%d/%m/%y %I:%M %p'), 'priority': task['priority']} for task in tasks_to_load]
                self.update_task_list()
            messagebox.showinfo("Load Tasks", "Tasks loaded successfully.")
        except (FileNotFoundError, json.JSONDecodeError):
            messagebox.showerror("Load Tasks", "No tasks found or file is corrupted.")

    def update_task_list(self):
        self.task_listbox.delete(0, tk.END)
        for task in self.tasks:
            self.task_listbox.insert(tk.END, f"{task['name']} - {task['due_date'].strftime('%d/%m/%y %I:%M %p')} - {task['priority']}")


 
    def schedule_reminders(self):
        if not self.tasks:
            messagebox.showwarning("No Tasks", "There are no tasks to set reminders for.")
            return

        reminder_window = tk.Toplevel(self.root)
        reminder_window.title("Select Tasks for Reminder")
        
        listbox = tk.Listbox(reminder_window, selectmode=tk.MULTIPLE)
        for idx, task in enumerate(self.tasks):
            listbox.insert(tk.END, f"{task['name']} - {task['due_date'].strftime('%d/%m/%y %I:%M %p')} - {task['priority']}")
        listbox.pack(padx=10, pady=10)
        
        
        def set_selected_reminders():
            selected_indices = listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("No Selection", "Please select at least one task for reminders.")
                return
            
            reminder_interval = simpledialog.askinteger("Reminder Interval", "Enter reminder interval in seconds", initialvalue=5)
            for idx in selected_indices:
                task = self.tasks[idx]
                time_until_due = (task['due_date'] - datetime.now()).total_seconds()
                if time_until_due > 0:
                    timer = Timer(reminder_interval, self.reminder_function, [task, reminder_interval])
                    self.reminder_timers.append(timer)
                    timer.start()
            reminder_window.destroy()
        
        ttk.Button(reminder_window, text="Set Reminders", command=set_selected_reminders).pack(pady=5)
    
    def stop_reminders(self):
        for timer in self.reminder_timers:
            timer.cancel()
        self.reminder_timers.clear()
        messagebox.showinfo("Stop Reminders", "All reminders have been stopped.")



    def reminder_function(self, task, interval):
        if (task['due_date'] - datetime.now()).total_seconds() > 0:
            priority_color = {'High': 'red', 'Medium': 'yellow', 'Low': 'green'}
            self.task_listbox.itemconfig(self.tasks.index(task), bg=priority_color.get(task['priority'], 'white'))
            message = f"Reminder: {task['name']} is due on {task['due_date'].strftime('%d/%m/%y %I:%M %p')} with {task['priority']} priority."
            messagebox.showinfo("Reminder", message)
            self.speak_message(message)
            timer = Timer(interval, self.reminder_function, [task, interval])
            self.reminder_timers.append(timer)
            timer.start()

    def speak_message(self, message):
        engine = pyttsx3.init()
        engine.say(message)
        engine.runAndWait()

    def show_consistency_graph(self):
        if not self.completed_tasks:
            messagebox.showinfo("Consistency Graph", "No tasks have been completed yet.")
            return
        dates = sorted(self.completed_tasks.keys())
        counts = [self.completed_tasks[date] for date in dates]
        
        plt.figure(figsize=(10, 5))
        plt.plot(dates, counts, marker='o')
        plt.xlabel('Date')
        plt.ylabel('Tasks Completed')
        plt.title('Task Completion Consistency')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskReminder(root)
    root.mainloop()
