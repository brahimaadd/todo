import psycopg2
from psycopg2 import OperationalError
import tkinter as tk
from tkinter import messagebox, ttk

# Configuration de la base de données
DB_NAME = "todo_db"
DB_USER = "postgres"  # Remplacez par votre utilisateur
DB_PASSWORD = "admin"  # Remplacez par votre mot de passe
DB_HOST = "localhost"


def create_connection():
    try:
        conn = psycopg2.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST
        )
        return conn
    except OperationalError as e:
        messagebox.showerror("Erreur", f"Impossible de se connecter à la base de données : {e}")
        return None

def get_all_tasks():
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, description, is_completed FROM tasks ORDER BY created_at;")
            tasks = cursor.fetchall()
            return tasks
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la récupération des tâches : {e}")
            return []
        finally:
            if conn:
                conn.close()

def add_task(description):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tasks (description) VALUES (%s) RETURNING id;", (description,))
            conn.commit()
            messagebox.showinfo("Succès", "Tâche ajoutée avec succès !")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ajout : {e}")
        finally:
            if conn:
                conn.close()

def update_task(task_id, new_description, is_completed):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tasks SET description = %s, is_completed = %s WHERE id = %s;",
                (new_description, is_completed, task_id)
            )
            conn.commit()
            messagebox.showinfo("Succès", "Tâche mise à jour !")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la mise à jour : {e}")
        finally:
            if conn:
                conn.close()

def delete_task(task_id):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
            conn.commit()
            messagebox.showinfo("Succès", "Tâche supprimée !")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la suppression : {e}")
        finally:
            if conn:
                conn.close()


class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("To-Do List avec PostgreSQL")
        self.root.geometry("600x400")

        # Style
        self.style = ttk.Style()
        self.style.configure("Treeview", rowheight=25)

        # Cadre principal
        self.frame = ttk.Frame(root)
        self.frame.pack(pady=10)

        # TTableau pour afficher les tâches
        self.tree = ttk.Treeview(
            self.frame,
            columns=("ID", "Description", "Status"),
            show="headings",
            selectmode="browse"
        )
        self.tree.heading("ID", text="ID")
        self.tree.heading("Description", text="Description")
        self.tree.heading("Status", text="Status")
        self.tree.column("ID", width=50)
        self.tree.column("Description", width=400)
        self.tree.column("Status", width=100)
        self.tree.pack()

        
        self.button_frame = ttk.Frame(root)
        self.button_frame.pack(pady=10)

       
        self.add_button = ttk.Button(self.button_frame, text="Ajouter", command=self.open_add_window)
        self.add_button.grid(row=0, column=0, padx=5)

        self.update_button = ttk.Button(self.button_frame, text="Modifier", command=self.open_update_window)
        self.update_button.grid(row=0, column=1, padx=5)

        self.delete_button = ttk.Button(self.button_frame, text="Supprimer", command=self.delete_task)
        self.delete_button.grid(row=0, column=2, padx=5)

        self.refresh_button = ttk.Button(self.button_frame, text="Rafraîchir", command=self.refresh_tasks)
        self.refresh_button.grid(row=0, column=3, padx=5)

        
        self.refresh_tasks()

    def refresh_tasks(self):
        
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        
        tasks = get_all_tasks()
        for task in tasks:
            status = "Terminée" if task[2] else "En cours"
            self.tree.insert("", "end", values=(task[0], task[1], status))

    def open_add_window(self):
        self.add_window = tk.Toplevel(self.root)
        self.add_window.title("Ajouter une tâche")

        ttk.Label(self.add_window, text="Description:").pack(pady=5)
        self.description_entry = ttk.Entry(self.add_window, width=40)
        self.description_entry.pack(pady=5)

        ttk.Button(
            self.add_window,
            text="Valider",
            command=lambda: [add_task(self.description_entry.get()), self.add_window.destroy(), self.refresh_tasks()]
        ).pack(pady=10)

    def open_update_window(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner une tâche à modifier.")
            return

        task_id = self.tree.item(selected_item)["values"][0]
        task_desc = self.tree.item(selected_item)["values"][1]
        task_status = self.tree.item(selected_item)["values"][2] == "Terminée"

        self.update_window = tk.Toplevel(self.root)
        self.update_window.title("Modifier une tâche")

        ttk.Label(self.update_window, text="Description:").pack(pady=5)
        self.update_desc_entry = ttk.Entry(self.update_window, width=40)
        self.update_desc_entry.insert(0, task_desc)
        self.update_desc_entry.pack(pady=5)

        self.status_var = tk.BooleanVar(value=task_status)
        ttk.Checkbutton(
            self.update_window,
            text="Terminée",
            variable=self.status_var
        ).pack(pady=5)

        ttk.Button(
            self.update_window,
            text="Valider",
            command=lambda: [
                update_task(task_id, self.update_desc_entry.get(), self.status_var.get()),
                self.update_window.destroy(),
                self.refresh_tasks()
            ]
        ).pack(pady=10)

    def delete_task(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner une tâche à supprimer.")
            return

        task_id = self.tree.item(selected_item)["values"][0]
        if messagebox.askyesno("Confirmer", "Voulez-vous vraiment supprimer cette tâche ?"):
            delete_task(task_id)
            self.refresh_tasks()


if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()