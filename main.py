import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox, ttk
import cx_Oracle
from PIL import Image, ImageTk

cx_Oracle.init_oracle_client(lib_dir=r"E:\Oracle Client Library v21")
connection = None
cursor = None
text_area = None
table_listbox = None
display_flag = None
right_frame = None
root = None

def conectare_bd(username, password, login_window):
    global connection, cursor
    try:
        connection = cx_Oracle.connect(username, password, "bd-dc.cs.tuiasi.ro:1539/orcl")
        cursor = connection.cursor()
        login_window.destroy()
        afisare_gui()
        return connection
    except cx_Oracle.DatabaseError as e:
        error_message = f"Eroare la conectarea la Oracle: {e}"
        messagebox.showerror("Eroare de conectare", error_message)
        return None

def logout(this_window_root):
    if this_window_root:
        this_window_root.destroy()
        login_gui()

def login_gui():
    def login():
        username = entry_username.get()
        password = entry_password.get()
        connection = conectare_bd(username, password, login_window)
        if connection:
            pass

    login_window = tk.Tk()
    login_window.title("Login")

    window_width = 400
    window_height = 200
    screen_width = login_window.winfo_screenwidth()
    screen_height = login_window.winfo_screenheight()
    x_coordinate = (screen_width - window_width) // 2
    y_coordinate = (screen_height - window_height) // 2
    login_window.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

    # Imaginea de fundal
    bg_image = tk.PhotoImage(file="imagine_joc.png")
    background_label = tk.Label(login_window, image=bg_image)
    background_label.place(x=0, y=0, relwidth=1, relheight=1)

    # Restul elementelor GUI
    label_username = tk.Label(login_window, text="Username", font=("Comic Sans MS", 14))
    label_username.pack()
    entry_username = tk.Entry(login_window, width=30)
    entry_username.pack()

    label_password = tk.Label(login_window, text="Password", font=("Comic Sans MS", 14))
    label_password.pack()
    entry_password = tk.Entry(login_window, show="*", width=30)
    entry_password.pack()

    button_login = tk.Button(login_window, text="Login", command=login, width=10, height=2)
    button_login.place(relx=0.5, rely=0.8, anchor=tk.CENTER)

    login_window.mainloop()


def show_table_content(table_name):
    try:
        global connection

        if connection is None:
            messagebox.showerror("Eroare", "Nu sunteți conectat la o bază de date Oracle.")
            return

        if table_name is None or not isinstance(table_name, str) or table_name.strip() == "":
            messagebox.showerror("Eroare", "Numele tabelului nu este valid.")
            return

        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        table_data = cursor.fetchall()

        cursor.execute(f"SELECT COLUMN_NAME FROM USER_TAB_COLUMNS WHERE TABLE_NAME = '{table_name}'")
        columns_info = cursor.fetchall()
        column_names = [col[0] for col in columns_info]

        cursor.close()

        if table_data:
            popup_window = tk.Toplevel()
            popup_window.title(f"Datele tabelului {table_name}")

            tree_view = ttk.Treeview(popup_window)
            tree_view['columns'] = tuple(column_names) if column_names else ("No data",)

            # Setarea antetelor coloanelor
            for col_name in column_names:
                tree_view.heading(col_name, text=col_name)

            for i, row in enumerate(table_data):
                tree_view.insert("", tk.END, text=i + 1, values=row)

            tree_view.pack(fill=tk.BOTH, expand=True)


    except cx_Oracle.DatabaseError as e:
        error_message = f"Eroare la citirea conținutului tabelului '{table_name}': {e}"
        messagebox.showerror("Eroare", error_message)


def show_tables():
    global connection
    if connection is None:
        messagebox.showerror("Eroare", "Nu sunteți conectat la o bază de date Oracle.")
        return

    table_list = get_tables(connection)
    if table_list:
        table_names = [table[0] for table in table_list]
        table_select_window = tk.Toplevel()
        table_select_window.title("Selectare tabel")

        # Configurare dimensiuni fereastră
        window_width = 600
        window_height = 400
        screen_width = table_select_window.winfo_screenwidth()
        screen_height = table_select_window.winfo_screenheight()
        x_coordinate = (screen_width - window_width) // 2
        y_coordinate = (screen_height - window_height) // 2
        table_select_window.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

        for table_name in table_names:
            table_button = tk.Button(
                table_select_window,
                text=table_name,
                command=lambda name=table_name: show_table_content(name),
                height=4,
                width=20
            )
            table_button.pack()

    else:
        messagebox.showinfo("Informație", "Nu există tabele în baza de date.")


def get_tables(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT table_name FROM user_tables")
        tables = cursor.fetchall()
        cursor.close()
        return tables
    except cx_Oracle.DatabaseError as e:
        error_message = f"Eroare la citirea tabelelor: {e}"
        messagebox.showerror("Eroare", error_message)
        return []

def inserare_in_baza():
    global connection

    if connection is None:
        messagebox.showerror("Eroare", "Nu sunteți conectat la o bază de date Oracle.")
        return

    def show_insert_menu(table_name, excluded_columns_str):
        try:
            cursor = connection.cursor()
            cursor.execute(f"SELECT COLUMN_NAME FROM USER_TAB_COLUMNS WHERE TABLE_NAME = '{table_name}'")
            columns_info = cursor.fetchall()
            cursor.close()

            insert_window = tk.Toplevel()
            insert_window.title(f"Inserare în tabelul {table_name}")

            entry_widgets = []

            # exclude specified columns
            columns_info = [col for col in columns_info if col[0] not in excluded_columns_str.split(',')]

            def insert_into_table():
                column_names = ", ".join([col[0] for col in columns_info])
                values = ", ".join([f"'{entry.get()}'" for entry in entry_widgets])
                query = f"INSERT INTO {table_name} ({column_names}) VALUES ({values}) ;"

                try:
                    cursor = connection.cursor()
                    cursor.execute(query)
                    connection.commit()
                    cursor.close()
                    messagebox.showinfo("Succes", "Datele au fost inserate cu succes!")
                except cx_Oracle.DatabaseError as e:
                    error_message = f"Eroare la inserarea datelor: {e}"
                    messagebox.showerror("Eroare", error_message)

            for i, (col_name,) in enumerate(columns_info):
                label = tk.Label(insert_window, text=f"Numele coloanei {col_name}:")
                label.grid(row=i, column=0)

                entry = tk.Entry(insert_window)
                entry.grid(row=i, column=1)
                entry_widgets.append(entry)

            insert_button = tk.Button(insert_window, text="Inserare", command=insert_into_table)
            insert_button.grid(row=len(columns_info), columnspan=2)

        except cx_Oracle.DatabaseError as e:
            error_message = f"Eroare la citirea informațiilor coloanelor pentru tabelul '{table_name}': {e}"
            messagebox.showerror("Eroare", error_message)

    table_list = get_tables(connection)
    if table_list:
        table_names = [table[0] for table in table_list]
        table_select_window = tk.Toplevel()
        table_select_window.title("Selectare tabel pentru inserare")

        for table_name in table_names:
            table_button = tk.Button(
                table_select_window,
                text=table_name,
                command=lambda name=table_name: show_exclude_columns_popup(name),
                height=4,
                width=20
            )
            table_button.pack()
    else:
        messagebox.showinfo("Informație", "Nu există tabele în baza de date.")

def show_insert_menu(table_name, excluded_columns_str):
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT COLUMN_NAME FROM USER_TAB_COLUMNS WHERE TABLE_NAME = '{table_name}'")
        columns_info = cursor.fetchall()
        cursor.close()

        insert_window = tk.Toplevel()
        insert_window.title(f"Inserare în tabelul {table_name}")

        entry_widgets = []

        # Exclude specified columns
        columns_info = [col for col in columns_info if col[0] not in excluded_columns_str.split(',')]

        def is_date(s):
            global cursor
            try:
                cursor.execute(f"SELECT TO_DATE('{s}', 'YYYY-MM-DD') FROM dual")
                return True
            except cx_Oracle.DatabaseError:
                return False

        def convert_to_date(s):
            global cursor
            cursor.execute(f"SELECT TO_DATE('{s}', 'YYYY-MM-DD') FROM dual")
            result = cursor.fetchone()[0]
            return result

        def insert_into_table():
            values = [entry.get() for entry in entry_widgets]
            converted_values = []

            for val in values:
                if val.isdigit():
                    converted_values.append(int(val))
                elif is_date(val):
                    converted_values.append(convert_to_date(val))
                else:
                    converted_values.append(val)

            column_names = ", ".join([col[0] for col in columns_info])
            placeholders = ", ".join([f":val{i+1}" for i in range(len(columns_info))])
            query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"

            params = {f"val{i+1}": val for i, val in enumerate(converted_values)}

            try:
                cursor = connection.cursor()
                cursor.execute(query, params)
                connection.commit()
                cursor.close()
                messagebox.showinfo("Succes", "Datele au fost inserate cu succes!")
            except cx_Oracle.DatabaseError as e:
                error_message = f"Eroare la inserarea datelor: {e}"
                messagebox.showerror("Eroare", error_message)

        for i, (col_name,) in enumerate(columns_info):
            label = tk.Label(insert_window, text=f"Numele coloanei {col_name}:")
            label.grid(row=i, column=0)

            entry = tk.Entry(insert_window)
            entry.grid(row=i, column=1)
            entry_widgets.append(entry)

        insert_button = tk.Button(insert_window, text="Inserare", command=insert_into_table)
        insert_button.grid(row=len(columns_info), columnspan=2)

    except cx_Oracle.DatabaseError as e:
        error_message = f"Eroare la citirea informațiilor coloanelor pentru tabelul '{table_name}': {e}"
        messagebox.showerror("Eroare", error_message)



def show_exclude_columns_popup(table_name):
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT COLUMN_NAME FROM USER_TAB_COLUMNS WHERE TABLE_NAME = '{table_name}'")
        columns_info = cursor.fetchall()
        cursor.close()

        exclude_columns_window = tk.Toplevel()
        exclude_columns_window.title(f"Excludere Coloane pentru {table_name}, SCRIE COLOANA CARE ESTE AUTOGENERATED")

        exclude_entry = tk.Entry(exclude_columns_window)
        exclude_entry.grid(row=0, column=0)

        def continue_with_exclusion():
            excluded_columns_str = exclude_entry.get()
            exclude_columns_window.destroy()
            show_insert_menu(table_name, excluded_columns_str)

        continue_button = tk.Button(exclude_columns_window, text="Continuare", command=continue_with_exclusion,width=100,height=10)
        continue_button.grid(row=0, column=1)

    except cx_Oracle.DatabaseError as e:
        error_message = f"Eroare la citirea informațiilor coloanelor pentru tabelul '{table_name}': {e}"
        messagebox.showerror("Eroare", error_message)


def show_delete_menu(table_name):
    try:
        global connection

        if connection is None:
            messagebox.showerror("Eroare", "Nu sunteți conectat la o bază de date Oracle.")
            return

        if table_name is None or not isinstance(table_name, str) or table_name.strip() == "":
            messagebox.showerror("Eroare", "Numele tabelului nu este valid.")
            return

        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        table_data = cursor.fetchall()

        cursor.execute(f"SELECT COLUMN_NAME FROM USER_TAB_COLUMNS WHERE TABLE_NAME = '{table_name}'")
        columns_info = cursor.fetchall()
        column_names = [col[0] for col in columns_info]

        cursor.close()

        if table_data:
            popup_window = tk.Toplevel()
            popup_window.title(f"Datele tabelului {table_name}")

            tree_view = ttk.Treeview(popup_window)
            tree_view['columns'] = tuple(column_names) if column_names else ("No data",)

            # Setarea antetelor coloanelor
            for col_name in column_names:
                tree_view.heading(col_name, text=col_name)

            for i, row in enumerate(table_data):
                tree_view.insert("", tk.END, text=i + 1, values=row)

            def delete_selected_row():
                selected_item = tree_view.selection()
                if selected_item:
                    row_id = int(selected_item[0][1:])  # Getting the row number from the item ID

                    # Get the column names from the Treeview
                    column_names = tree_view['columns']

                    # Loop through the columns to find the primary key column
                    primary_key_column = None
                    for col in column_names:
                        # Checking if the column ends with "_id"
                        if col.lower().endswith('_id'):
                            primary_key_column = col
                            break  # Once found, stop the loop

                    if primary_key_column:
                        delete_from_table(table_name, primary_key_column, row_id)
                    else:
                        messagebox.showerror("Eroare", "Nu s-a putut determina coloana cheii primare.")

            delete_button = tk.Button(popup_window, text="Șterge", command=delete_selected_row)
            delete_button.pack()

            tree_view.pack(fill=tk.BOTH, expand=True)


    except cx_Oracle.DatabaseError as e:
        error_message = f"Eroare la citirea conținutului tabelului '{table_name}': {e}"
        messagebox.showerror("Eroare", error_message)

def delete_from_table(table_name, primary_key_column, row_id):
    try:
        global connection

        if connection is None:
            messagebox.showerror("Eroare", "Nu sunteți conectat la o bază de date Oracle.")
            return

        if table_name is None or not isinstance(table_name, str) or table_name.strip() == "":
            messagebox.showerror("Eroare", "Numele tabelului nu este valid.")
            return

        if primary_key_column is None or not isinstance(primary_key_column, str) or primary_key_column.strip() == "":
            messagebox.showerror("Eroare", "Numele coloanei cheii primare nu este valid.")
            return

        if row_id is None or not isinstance(row_id, int):
            messagebox.showerror("Eroare", "ID-ul rândului nu este valid.")
            return

        cursor = connection.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE {primary_key_column} = :1", (row_id,))
        connection.commit()
        cursor.close()
        messagebox.showinfo("Succes", "Rândul a fost șters cu succes!")

    except cx_Oracle.DatabaseError as e:
        error_message = f"Eroare la ștergerea rândului din tabelul '{table_name}': {e}"
        messagebox.showerror("Eroare", error_message)

def show_tables_for_delete():
    global connection
    if connection is None:
        messagebox.showerror("Eroare", "Nu sunteți conectat la o bază de date Oracle.")
        return

    table_list = get_tables(connection)
    if table_list:
        table_names = [table[0] for table in table_list]
        table_select_window = tk.Toplevel()
        table_select_window.title("Selectare tabel")

        # Configurare dimensiuni fereastră
        window_width = 600
        window_height = 400
        screen_width = table_select_window.winfo_screenwidth()
        screen_height = table_select_window.winfo_screenheight()
        x_coordinate = (screen_width - window_width) // 2
        y_coordinate = (screen_height - window_height) // 2
        table_select_window.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

        for table_name in table_names:
            table_button = tk.Button(
                table_select_window,
                text=table_name,
                command=lambda name=table_name: show_delete_menu(name),
                height=4,
                width=20
            )
            table_button.pack()

    else:
        messagebox.showinfo("Informație", "Nu există tabele în baza de date.")


def show_update_menu():
    try:
        global connection

        if connection is None:
            messagebox.showerror("Eroare", "Nu sunteți conectat la o bază de date Oracle.")
            return

        cursor = connection.cursor()

        cursor.execute("SELECT table_name FROM user_tables")
        table_names = [row[0] for row in cursor.fetchall()]
        cursor.close()

        if table_names:
            update_table_window = tk.Toplevel()
            update_table_window.title("Selectati tabelul pentru actualizare")

            table_listbox = tk.Listbox(update_table_window,width=100,height=15)
            for table_name in table_names:
                table_listbox.insert(tk.END, table_name)

            def select_table():
                selected_table_index = table_listbox.curselection()
                if selected_table_index:
                    selected_table = table_listbox.get(selected_table_index)
                    update_table_window.destroy()
                    show_update_row(selected_table)

            select_button = tk.Button(update_table_window, text="Selectare tabel", command=select_table)
            select_button.pack()

            table_listbox.pack()
            update_table_window.mainloop()
        else:
            messagebox.showinfo("Informație", "Nu există tabele în baza de date.")

    except cx_Oracle.DatabaseError as e:
        error_message = f"Eroare la citirea numelor de tabel din baza de date: {e}"
        messagebox.showerror("Eroare", error_message)

def update_values(table_name, column_names, row_id, new_values):
    try:
        global connection

        if connection is None:
            messagebox.showerror("Eroare", "Nu sunteți conectat la o bază de date Oracle.")
            return

        if (not isinstance(table_name, str)) or (not table_name.strip()):
            messagebox.showerror("Eroare", "Numele tabelului nu este valid.")
            return

        if (not isinstance(row_id, int)) or row_id < 1:
            messagebox.showerror("Eroare", "ID-ul rândului nu este valid.")
            return

        if not isinstance(new_values, list):
            messagebox.showerror("Eroare", "Noile valori nu sunt valide.")
            return

        cursor = connection.cursor()

        # Construct the UPDATE query
        update_query = f"UPDATE {table_name} SET "
        for i, col_name in enumerate(column_names):
            update_query += f"{col_name} = :{i+1}, "
        update_query = update_query[:-2]  # Remove the last comma and space
        update_query += f" WHERE rowid = :{len(column_names) + 1}"

        # Create a tuple of values for the query
        values_tuple = tuple(new_values) + (row_id,)

        # Execute the UPDATE query
        cursor.execute(update_query, values_tuple)
        connection.commit()

        messagebox.showinfo("Succes", "Rândul a fost actualizat cu succes!")

        cursor.close()

    except cx_Oracle.DatabaseError as e:
        error_message = f"Eroare la actualizarea rândului în tabela '{table_name}': {e}"
        messagebox.showerror("Eroare", error_message)

def show_update_row(table_name):
    def is_date(s):
        global cursor
        try:
            cursor.execute(f"SELECT TO_DATE('{s}', 'YYYY-MM-DD') FROM dual")
            return True
        except cx_Oracle.DatabaseError:
            return False

    def convert_to_date(s):
        global cursor
        cursor.execute(f"SELECT TO_DATE('{s}', 'YYYY-MM-DD') FROM dual")
        result = cursor.fetchone()[0]
        return result

    def update_selected_row():
        selected_rows = tree_view.selection()
        if selected_rows:
            selected_row_id = selected_rows[0]
            new_values = []

            for i, entry in enumerate(entry_widgets):
                value = entry.get()
                # Verificăm dacă valoarea introdusă este o dată și o convertim la formatul dorit
                if is_date(value):
                    new_values.append(convert_to_date(value))
                else:
                    new_values.append(value)

            update_values(table_name, column_names, int(selected_row_id), new_values)
        else:
            messagebox.showwarning("Avertizare", "Nu a fost selectat niciun rând pentru actualizare.")
    try:
        global connection

        if connection is None:
            messagebox.showerror("Eroare", "Nu sunteți conectat la o bază de date Oracle.")
            return

        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        table_data = cursor.fetchall()

        cursor.execute(f"SELECT COLUMN_NAME FROM USER_TAB_COLUMNS WHERE TABLE_NAME = '{table_name}'")
        columns_info = cursor.fetchall()
        column_names = [col[0] for col in columns_info]
        cursor.close()

        if table_data:
            update_row_window = tk.Toplevel()
            update_row_window.title(f"Selectați rândul pentru actualizare din tabelul {table_name}")

            tree_view = ttk.Treeview(update_row_window)
            tree_view['columns'] = column_names

            for col_name in column_names:
                tree_view.heading(col_name, text=col_name)

            for row in table_data:
                tree_view.insert('', tk.END, values=row)

            tree_view.pack(fill=tk.BOTH, expand=True)

            entry_widgets = []
            for i, col_name in enumerate(column_names):
                label = tk.Label(update_row_window, text=f"{col_name}:")
                label.pack()

                entry = tk.Entry(update_row_window)
                entry.pack()
                entry.insert(0, table_data[0][i])
                entry_widgets.append(entry)

            update_button = tk.Button(update_row_window, text="Actualizare", command=update_selected_row)
            update_button.pack()

        else:
            messagebox.showinfo("Informație", "Nu există rânduri în tabelul selectat.")

    except cx_Oracle.DatabaseError as e:
        error_message = f"Eroare la citirea conținutului tabelului '{table_name}': {e}"
        messagebox.showerror("Eroare", error_message)









def animation(count):
    global label_table_list,im, frames
    im2 = im[count]
    label_table_list.configure(image=im2)
    count += 1
    if count == frames:
        count = 0
    root.after(50,animation(count))
def afisare_gui():
    global text_area, table_listbox, right_frame

    root = tk.Tk()
    root.title("Oracle Database GUI")
    root.configure(bg='#FA8072')

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    frame_width = int(screen_width * 0.75)
    frame_height = int(screen_height * 0.75)
    root.geometry(f"{frame_width}x{frame_height}+{int((screen_width - frame_width) / 2)}+{int((screen_height - frame_height) / 2)}")

    # Configurație coloane
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=2)

    left_frame = tk.Frame(root, bg='#2E86C1')
    left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")

    display_button = tk.Button(left_frame, text="Afiseaza Tabele", command=show_tables)
    display_button.pack(fill=tk.X, pady=5)

    display_button = tk.Button(left_frame, text="Insereaza in Tabele", command=inserare_in_baza)
    display_button.pack(fill=tk.X, pady=5)

    display_button = tk.Button(left_frame, text="Update Date", command=show_update_menu)
    display_button.pack(fill=tk.X, pady=5)

    delete_button = tk.Button(left_frame, text="Șterge din Tabele", command=show_tables_for_delete)
    delete_button.pack(fill=tk.X, pady=5)

    logout_button = tk.Button(left_frame, text="Log Out", command=lambda: logout(root))
    logout_button.pack(fill=tk.X, pady=5)

    table_names = cursor.execute("SELECT table_name FROM user_tables").fetchall()
    table_names = [name[0] for name in table_names]

    image = Image.open("merg_gabene.png")
    tk_image = ImageTk.PhotoImage(image)
    label_table_list = tk.Label(root, image=tk_image)
    label_table_list.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

    label_table_list_2 = tk.Label(root, text="Shop On-Line: Abur!", font=('Comic Sans MS', 60),fg ='#FAEF5D',bg='#1D2B53',bd=2)
    label_table_list_2.grid(row=2, column=1, padx=10, pady=5)

    table_frame = tk.Frame(root, bg='#2E86C1', width=10, height=10)
    table_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nswe")

    label_lista_tabele = tk.Label(table_frame, text="Lista Tabele", font=('Arial', 14), bg='#2E86C1', fg='white')
    label_lista_tabele.pack()

    table_listbox = tk.Listbox(table_frame, selectmode=tk.SINGLE)
    for name in table_names:
        table_listbox.insert(tk.END, name)
    table_listbox.pack()

    root.mainloop()

if __name__ == "__main__":
    login_gui()
