import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from tkinter import simpledialog
import sqlite3
import hashlib
from PIL import Image, ImageTk
import tempfile
import reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import webbrowser 
from datetime import datetime, timedelta
from io import BytesIO
import os
import sys

db_path = "supermarket.db"
os.chdir(os.path.dirname(os.path.abspath(__file__)))
        #load the logo image
def load_logo(parent):
    try:
        logo_path = r"C:\Users\hp\prog demo\SUPER.png"  
        img = Image.open(logo_path).resize((150, 150))
        logo = ImageTk.PhotoImage(img)
        label = tk.Label(parent, image=logo, bg=parent["bg"])
        label.image = logo  
        label.pack(pady=10)
    except Exception as e:
        tk.Label(parent, text="Logo not found", font=("Arial", 14), bg=parent["bg"]).pack(pady=10)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def restart_app():
    root.destroy()
    os.execl(sys.executable, sys.executable, *sys.argv)


def setup_database():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quantity INTEGER,
        Name TEXT,
        Brand TEXT,
        Batch_number INTEGER,
        Unit_price REAL,
        expiry_date TEXT      
    )''')
    c.execute("PRAGMA table_info(stock)")
    columns= [col[1]for col in c.fetchall()]
    if "expiry_date" not in columns:
        c.execute("ALTER TABLE stock ADD COLUMN expiry_date TEXT")

    c.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        Name TEXT,
        Brand TEXT,
        Batch_number INTEGER,
        quantity INTEGER,
        Unit_price REAL,
        subtotal REAL,
        grand_total REAL,
        cashier TEXT,
        sale_time TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS blocked_users (
        username TEXT PRIMARY KEY
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS login_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        login_time TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS app_state (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')

    if not c.execute("SELECT * FROM users WHERE username='admin'").fetchone():
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", hash_password("password123")))
    if not c.execute("SELECT * FROM app_state WHERE key='admin_logged_in'").fetchone():
        c.execute("INSERT INTO app_state (key, value) VALUES ('admin_logged_in', 'no')")

    conn.commit()
    conn.close()

# ---------- LOGIN ----------
def login():
    user = username_entry.get().strip()
    pwd = password_entry.get().strip()
    hashed = hash_password(pwd)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    if c.execute("SELECT 1 FROM blocked_users WHERE username=?", (user,)).fetchone():
        messagebox.showerror("Access Denied", "Your account has been blocked.")
        conn.close()
        return

    if user == "admin":
        if hashed == hash_password("password123"):
            c.execute("UPDATE app_state SET value='yes' WHERE key='admin_logged_in'")
            c.execute("INSERT INTO login_history (username, login_time) VALUES (?, ?)",
                      (user, f"Logged in at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
            conn.commit()
            conn.close()
            show_welcome_screen(user)
            return
        else:
            messagebox.showerror("Login Failed", "Incorrect admin password.")
            conn.close()
            return

    # Normal user login
    if not user or not pwd:
        messagebox.showerror("input error", "fill all fields.")
        conn.close()
        return
    if c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, hashed)).fetchone():
        c.execute("INSERT INTO login_history (username, login_time) VALUES (?, ?)",
                  (user, f"Logged in at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
        conn.commit()
        conn.close()
        show_welcome_screen(user)
    else:
        messagebox.showerror("Login Failed", "Incorrect credentials.")
        password_entry.delete(0, tk.END)
        conn.close()
def open_registration():
    def register():
        user = reg_username.get()
        pwd = reg_password.get()
        if not user or not pwd:
            messagebox.showerror("Input Error", "Fill all fields.")
            return
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, hash_password(pwd)))
            conn.commit()
            messagebox.showinfo("Success", "User registered.")
            reg_win.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username exists.")
        finally:
            conn.close()

    reg_win = tk.Toplevel(root)
    reg_win.title("Register")
    reg_win.geometry("300x250")
    reg_win.configure(bg="lightblue")
    load_logo(reg_win)

    tk.Label(reg_win, text="Username", bg="lightblue").pack()
    reg_username = tk.Entry(reg_win)
    reg_username.pack()

    tk.Label(reg_win, text="Password", bg="lightblue").pack()
    reg_password = tk.Entry(reg_win, show="*")
    reg_password.pack()

    tk.Button(reg_win, text="Register", command=register).pack(pady=22)

# ---------- WELCOME ----------
def show_welcome_screen(username):
    for widget in root.winfo_children():
        widget.destroy()
    root.configure(bg="orange")
    load_logo(root)
    tk.Label(root, text=f"Welcome {username}", font=("Arial", 22, "bold"), bg="orange").pack(pady=20)

    tk.Button(root, text="View Stock", font=("Arial", 16), width=20, command=lambda: view_stock_window(username)).pack(pady=10)
    tk.Button(root, text="Buy Item", font=("Arial", 16), width=20, command=lambda: buy_item_window(username)).pack(pady=10)
    tk.Button(root, text="Reset APP", font=("Arial", 12), bg="Green", fg="white", command=restart_app).pack(pady=5)

    if username == "admin":
        tk.Button(root, text="Manage Members", bg="blue", fg="white", command=manage_members_window).pack(pady=10)

    tk.Button(root, text="Logout", font=("Arial", 14), bg="red", fg="white", command=return_to_login).pack(pady=20)
 
def return_to_login():
    for widget in root.winfo_children():
        widget.destroy()
    root.configure(bg="purple")
    load_logo(root)

    tk.Label(root, text="Please Login", font=("Arial", 24, "bold"), fg="white", bg="purple").pack(pady=10)
    tk.Label(root, text="Username:", bg="purple", fg="white").pack()
    global username_entry, password_entry  # Make sure these are global so login() can access them
    username_entry = tk.Entry(root, font=("Arial", 14))
    username_entry.pack()
    tk.Label(root, text="Password:", bg="purple", fg="white").pack()
    password_entry = tk.Entry(root, show="*", font=("Arial", 14))
    password_entry.pack()
    tk.Button(root, text="Login", font=("Arial", 14), command=login).pack(pady=10)
    tk.Button(root, text="Register", font=("Arial", 12), command=open_registration).pack()
    tk.Button(root, text="Exit", bg="red", fg="white", command=root.destroy).pack(pady=5)

    username_entry.focus()
    #.............MANAGE_MEMBERS.........................
def manage_members_window():
    admin_win = tk.Toplevel(root)
    admin_win.title("Manage Members")
    admin_win.geometry("600x500")
    admin_win.configure(bg="lightgrey")
    load_logo(admin_win)

    members_list = tk.Listbox(admin_win, font=("Arial", 12), width=40)
    members_list.pack(pady=10)

    def load_members():
        members_list.delete(0, tk.END)
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        for row in c.execute("SELECT username FROM users WHERE username != 'admin'"):
            status = "BLOCKED" if c.execute("SELECT 1 FROM blocked_users WHERE username=?", (row[0],)).fetchone() else "ACTIVE"
            members_list.insert(tk.END, f"{row[0]} ({status})")
        conn.close()

    def block_member():
        selection = members_list.curselection()
        if not selection: return
        username = members_list.get(selection[0]).split()[0]
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO blocked_users (username) VALUES (?)", (username,))
        conn.commit()
        conn.close()
        load_members()
        messagebox.showinfo("Member Blocked", f"{username} has been blocked.")

    def unblock_member():
        selection = members_list.curselection()
        if not selection: return
        username = members_list.get(selection[0]).split()[0]
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("DELETE FROM blocked_users WHERE username=?", (username,))
        conn.commit()
        conn.close()
        load_members()
        messagebox.showinfo("Member Unblocked", f"{username} is now active.")

    def dismiss_member():
        selection = members_list.curselection()
        if not selection: return
        username = members_list.get(selection[0]).split()[0]
        confirm = messagebox.askyesno("Confirm", f"Dismiss {username}?")
        if confirm:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("DELETE FROM users WHERE username=?", (username,))
            c.execute("DELETE FROM blocked_users WHERE username=?", (username,))
            conn.commit()
            conn.close()
            load_members()
            messagebox.showinfo("Member Dismissed", f"{username} removed.")

    def view_activity():
        selection = members_list.curselection()
        if not selection:
            return
        username = members_list.get(selection[0]).split()[0]
        
        activity_win = tk.Toplevel(admin_win)
        activity_win.title("Activity Report")
        activity_win.geometry("450x350")
        activity_win.configure(bg="white")

        tk.Label(activity_win, text=f"Activity Report for {username}", font=("Arial", 14, "bold"), bg="white").pack(pady=10)

        report_list = tk.Listbox(activity_win, width=60)
        report_list.pack(pady=10)

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        for row in c.execute("SELECT login_time FROM login_history WHERE username=? ORDER BY id DESC", (username,)):
            report_list.insert(tk.END, row[0])
        conn.close()

        if report_list.size() == 0:
            report_list.insert(tk.END, "No activity recorded for this user.")

    def view_all_members():
        view_all_members_win = tk.Toplevel(admin_win)
        view_all_members_win.title("All Registered Members")
        view_all_members_win.geometry("350x400")
        view_all_members_win.configure(bg="white")
        tk.Label(view_all_members_win, text="All Registered Members", font=("Arial", 14, "bold"), bg="white").pack(pady=10)
        listbox = tk.Listbox(view_all_members_win, width=40)
        listbox.pack(pady=10, fill=tk.BOTH, expand=True)
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        for row in c.execute("SELECT username FROM users"):
            listbox.insert(tk.END, row[0])
        conn.close()

        def delete_selected_member():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a member to delete.")
                return
            username = listbox.get(selection[0])
            if username == "admin":
                messagebox.showerror("Error", "Cannot delete admin user.")
                return
            confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{username}'?")
            if confirm:
               conn = sqlite3.connect(db_path)
               c = conn.cursor()
               c.execute("DELETE FROM users WHERE username=?", (username,))
               c.execute("DELETE FROM blocked_users WHERE username=?", (username,))
               conn.commit()
               conn.close()
               listbox.delete(selection[0])
               messagebox.showinfo("Deleted", f"Member '{username}' deleted.")

        tk.Button(view_all_members_win, text="Delete Selected Member", command=delete_selected_member, bg="red", fg="white").pack(pady=8)

    # --- Buttons in one horizontal line ---
    btn_frame = tk.Frame(admin_win, bg="lightgrey")
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Block", command=block_member, width=12).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="Unblock", command=unblock_member, width=12).grid(row=0, column=1, padx=5)
    tk.Button(btn_frame, text="Dismiss", command=dismiss_member, width=12).grid(row=0, column=2, padx=5)
    tk.Button(btn_frame, text="View Activity", command=view_activity, width=12).grid(row=0, column=3, padx=5)
    tk.Button(btn_frame, text="View All Members", command=view_all_members, width=15).grid(row=0, column=4, padx=5)
    tk.Button(btn_frame, text="Exit", command=lambda: (admin_win.destroy(), root.deiconify()), width=12).grid(row=0, column=5, padx=5)

    load_members()
    root.withdraw()
# ---------- STOCK WINDOW ----------
def view_stock_window(username):
    root.withdraw()
    stock_win = tk.Toplevel(root)
    stock_win.title("Supermarket Stock")
    stock_win.geometry("800x600")
    stock_win.configure(bg="lightyellow")
    load_logo(stock_win)

    tk.Label(stock_win, text="STOCK LIST", font=("Arial", 18, "bold"), bg="lightyellow").pack(padx=10)

    frame = tk.Frame(stock_win)
    frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    tree = ttk.Treeview(frame, columns=( "id", "quantity", "Name", "Brand", "Batch_number", "Unit_price", "expiry_date"), show="headings", yscrollcommand=scrollbar.set)
    for col in ["id", "quantity", "Name", "Brand", "Batch_number", "Unit_price", "expiry_date"]:
        tree.heading(col, text=col)
        tree.column(col, anchor=tk.CENTER)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=tree.yview)

    def load_stock():
        tree.delete(*tree.get_children())
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        for row in c.execute("SELECT id, quantity, Name, Brand, Batch_number, Unit_price, expiry_date FROM stock"):
            tree.insert("", tk.END, values=row)
        conn.close()
        check_expiry_warnings()

    def check_expiry_warnings():
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        today = datetime.now().date()
        soon = today + timedelta(days=7)  # Warn if expiring within 7 days
        expired_items = []
        expiring_soon = []
        for row in c.execute("SELECT Name, expiry_date FROM stock"):
            name, expiry = row
            try:
                expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
                if expiry_date < today:
                    expired_items.append(name)
                elif today <= expiry_date <= soon:
                    expiring_soon.append(name)
            except Exception:
                  continue
        conn.close()
        if expired_items:
            messagebox.showwarning("Expired Items", f"Expired: {', '.join(expired_items)}")
        if expiring_soon:
            messagebox.showwarning("Expiring Soon", f"Expiring soon: {', '.join(expiring_soon)}")

    def add_item():
        popup = tk.Toplevel(stock_win)
        popup.title("Add Item")
        popup.geometry("300x400")
        popup.configure(bg="lightblue")

        entries = {}
        for label in ["quantity", "Name", "Brand", "Batch_number", "Unit_price", "expiry_date"]:
            tk.Label(popup, text=label, bg="lightblue").pack()
            entry = tk.Entry(popup)
            entry.pack()
            entries[label] = entry

        def save():
            try:
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute(
                    "INSERT INTO stock (quantity, Name, Brand, Batch_number, Unit_price, expiry_date) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                           int(entries["quantity"].get()),
                           entries["Name"].get(),
                           entries["Brand"].get(),
                           entries["Batch_number"].get(),
                           float(entries["Unit_price"].get()),
                           entries["expiry_date"].get()
                    )
                )
                
                c.execute("INSERT INTO login_history (username, login_time) VALUES (?, ?)",
                  (username, f"Added item '{entries['Name'].get()}' at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
                conn.commit()
                conn.close()
                popup.destroy()
                load_stock()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {e}")

        tk.Button(popup, text="Save", command=save).pack(padx=10)        
    def delete_item():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No section", "pease select an item to deete")
            return
        values = tree.item(selected[0])['values']
        item_id = values[0]
        confirm = messagebox.askyesno("confirm Delete", f"Are you sure you want to delete item '{values[2]}'?")
        if confirm:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("DELETE FROM stock WHERE id = ?", (item_id,))
            conn.commit()
            conn.close()
            load_stock()
            messagebox.showinfo("Deleted", f"Item deleted successfully.")

    def update_item():
        selected = tree.selection()
        if not selected:
           messagebox.showwarning("No selection", "pease seect an item to update")
           return
        values = tree.item(selected[0])['values']
        item_id, quantity, Name, Brand, Batch_number, Unit_price, expiry_date = values  # <-- add expiry_date

        popup = tk.Toplevel(stock_win)
        popup.title("Update Item")
        popup.geometry("300x400")
        popup.configure(bg="lightgreen")
        tk.Label(popup, text="Quantity", bg="lightblue").pack()
        qty_entry = tk.Entry(popup)
        qty_entry.insert(0, str(quantity))
        qty_entry.pack()

        tk.Label(popup, text="Unit_price", bg="lightblue").pack()
        price_entry = tk.Entry(popup)
        price_entry.insert(0, float(Unit_price))
        price_entry.pack()

        tk.Label(popup, text="Expiry Date (YYYY-MM-DD)", bg="lightblue").pack()
        expiry_entry = tk.Entry(popup)
        expiry_entry.insert(0, expiry_date)
        expiry_entry.pack()

        def save_updates():
            try:
                new_qty = int(qty_entry.get())
                new_price = float(price_entry.get())
                new_expiry = expiry_entry.get()
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute("UPDATE stock SET quantity = ?, Unit_price = ?, expiry_date = ? WHERE id = ?",
                      (new_qty, new_price, new_expiry, item_id))
                conn.commit()
                conn.close()
                popup.destroy()
                load_stock()
                messagebox.showinfo("Updated", f"Item updated successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"invalid input: {e}")

        tk.Button(popup, text="Save", command=save_updates).pack(padx=10)

    btn_frame = tk.Frame(stock_win,bg="lightyellow")
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Add Item", command=add_item).grid(row=0, column=0,padx=5)
    tk.Button(btn_frame, text="Delete Item", command=delete_item, bg= "red", fg= "white",).grid(row=0, column=1, padx=5)
    tk.Button(btn_frame, text="Update Item", command=update_item, bg="blue", fg="white").grid(row=0, column=2, padx=5)
    tk.Button(btn_frame, text="Exit", bg="red", fg="white", command=lambda: (stock_win.destroy(), root.deiconify())).grid(row=0, column=3,padx=5)

    load_stock()
#...............buy item window..................
db_path = "supermarket.db"

def buy_item_window(username):
    buy_win = tk.Toplevel()
    buy_win.title("Buy Item")
    buy_win.geometry("950x750")
    buy_win.configure(bg="lightgreen")
    load_logo(buy_win)

    shopping_list = []
    total_var = tk.StringVar(value="0")

    # ───── Load stock from database ─────
    def load_stock():
        for row in tree.get_children():
            tree.delete(row)
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT  id, quantity, Name, Brand, Batch_number, Unit_price FROM stock")
            for item in cur.fetchall():
                tree.insert("", tk.END, values=item)

    # ───── Add Item to Shopping List ─────
    def add_item():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an item.")
            return

        values = tree.item(selected[0])['values']
        id, quantity, Name, Brand, Batch_number, Unit_price = values
        quantity= int(quantity)
        Unit_price= float(Unit_price)

        try:
            qty = simpledialog.askinteger("Quantity", f"Enter quantity to buy (Available: {quantity}):", minvalue=1)
            if qty is None:
                return
            if qty > quantity:
                messagebox.showerror("Insufficient Stock", "Not enough stock available.")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
            return

        # Add to shopping list
        print("Adding to shopping list:", {
        "id": id,
        "quantity": qty,
        "Name": Name,
        "Brand": Brand,
        "Batch_number": Batch_number,
        "Unit_price": Unit_price,
        "subtotal": Unit_price * qty
        })
        shopping_list.append({
            "id": id,
            "quantity": qty,
            "Name": Name,
            "Brand": Brand,
            "Batch_number": Batch_number,
            "Unit_price": Unit_price,
            "subtotal": Unit_price * qty
        })
    
        # Reduce stock in DB
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("UPDATE stock SET quantity = quantity - ? WHERE id = ?",
                        (qty, id))
            conn.commit()
        load_stock()
        update_list()

    # ───── Update shopping list display ─────
    def update_list():
        print("Updating shopping list", shopping_list)
        shop_tree.delete(*shop_tree.get_children())
        for item in shopping_list:
            shop_tree.insert("", tk.END, values=(
                item["id"],
                item["quantity"],
                item["Name"], item["Brand"], item["Batch_number"],
                item["Unit_price"], item["subtotal"]
            ))

    # ───── Remove item from Shopping List ─────
    def delete_item():
        selected = shop_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an item to delete.")
            return
        index = shop_tree.index(selected[0])
        item = shopping_list.pop(index)
        # Restore stock
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("UPDATE stock SET quantity = quantity + ? WHERE id = ?",
                        (item["quantity"], item["id"]))
            conn.commit()
        load_stock()
        update_list()

    def show_total():
    
        total = sum(item["subtotal"] for item in shopping_list)
        total_var.set(str(total))
        messagebox.showinfo("Total Price", f"Total amount: {total}")

    def print_receipt():
        if not shopping_list:
            messagebox.showwarning("No Items", "Add items before printing a receipt.")
            return

        sales_time = datetime.now()
        date_str = sales_time.strftime("%Y-%m-%d %H:%M:%S")
        total = sum(item["subtotal"] for item in shopping_list)
        total_var.set(str(total))
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        receipt_path = temp_file.name

        c = canvas.Canvas(receipt_path, pagesize=A4)
        width, height = A4

        y = height - 50
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, y, "SUPER MARKET RECEIPT")
        y -= 30

        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Seller: {username}")
        c.drawRightString(width - 50, y, f"Date: {date_str}")
        y -= 20
        c.drawString(50, y, "Customer Name: ___________________________")
        y -= 20

        c.line(50, y, width - 50, y)
        y -= 20

        headers = ["id", "quantity", "Name", "Brand", "Batch_number", "Unit_Price", "Subtotal"]
        col_widths = [60, 60, 60, 80, 80, 60, 60]
        x_positions = [50]
        for w in col_widths[:-1]:
            x_positions.append(x_positions[-1] + w)

        c.setFont("Helvetica-Bold", 9)
        for i, h in enumerate(headers):
            c.drawString(x_positions[i], y, h)
        y -= 15
        c.setFont("Helvetica", 9)

        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
        for item in shopping_list:
            cur.execute(
                "INSERT INTO sales (item_id, quantity,Name, Brand, Batch_number, Unit_price, subtotal, cashier, sale_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (item["id"], item["quantity"], item["Name"], item["Brand"], item["Batch_number"], item["Unit_price"], item["subtotal"],
                  username, sales_time.strftime("%Y-%m-%d %H:%M:%S")
                )
            )

            data = [
                str(item["id"]),
                str(item["quantity"]), str(item["Name"]), str(item["Brand"]), str(item["Batch_number"]),
                f"{item['Unit_price']:.2f}", f"{item['subtotal']:.2f}"
            ]
            for i, d in enumerate(data):
                c.drawString(x_positions[i], y, d)
            y -= 15
            if y < 100:
                c.showPage()
                y = height - 50
        conn.commit()

        y -= 10
        c.line(50, y, width - 50, y)
        y -= 25

        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(width - 50, y, f"Total: UGX {total}")
        y -= 40

        c.setFont("Helvetica", 10)
        c.drawString(50, y, "Signature: ____________________")
        c.drawRightString(width - 50, y, "Official Stamp")

        c.save()

        webbrowser.open_new(receipt_path)
        messagebox.showinfo("Receipt Saved", "Receipt saved and ready for printing.")
        
    def exit_window():
        buy_win.destroy()

    # ───── Stock Treeview ─────
    tree_frame = tk.Frame(buy_win)
    tree_frame.pack(pady=10)

    tree_scroll = tk.Scrollbar(tree_frame)
    tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    tree = ttk.Treeview(
        tree_frame,
        yscrollcommand=tree_scroll.set,
        columns=("id", "quantity", "Name", "Brand", "Batch_number", "Unit_price"),
        show="headings",
        height=8
    )
    tree.pack()

    for col in ("id", "quantity", "Name", "Brand", "Batch_number", "Unit_price"):
        tree.heading(col, text=col)
        tree.column(col, anchor=tk.CENTER)

    tree_scroll.config(command=tree.yview)

    #______view daily sales____________
    def view_daily_sales():
        sales_win = tk.Toplevel(root)
        sales_win.title("Today's Sales")
        sales_win.geometry("900x500")
        sales_win.configure(bg="lightyellow")
        load_logo(sales_win)

        tree = ttk.Treeview(sales_win, columns=("quantity", "Name", "Brand", "Batch_number", "Unit_price", "subtotal", "cashier", "sale_time"), show="headings")
        for col in ("quantity", "Name", "Brand", "Batch_number", "Unit_price", "subtotal", "cashier", "sale_time"):
            tree.heading(col, text=col)
            tree.column(col, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True)

        today = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        total = 0
        for row in c.execute("SELECT quantity, Name, Brand, Batch_number,  Unit_price, subtotal, cashier, sale_time FROM sales WHERE sale_time LIKE ?", (today+"%",)):
            tree.insert("", tk.END, values=row)
            total += row[5] 
        conn.close()
        tk.Label(sales_win, text=f"Total sales for {today}: UGX {total:.2f}", font=("Arial", 14, "bold"), bg="lightyellow").pack(pady=10)
        tk.Button(sales_win, text="Exit", command=lambda: sales_win.destroy(), bg="red", fg="white").pack(pady=10)

    # ───── Shopping List Treeview ─────
    tk.Label(buy_win, text="Shopping List", bg="lightgreen", font=("Arial", 14)).pack()
    shop_frame = tk.Frame(buy_win)
    shop_frame.pack()

    shop_tree = ttk.Treeview(
        shop_frame,
        columns=("id", "quantity", "Name", "Brand", "Batch_number", "Unit_price", "subtotal"),
        show="headings",
        height=10
    )
    shop_tree.pack()

    for col in ("id", "quantity", "Name", "Brand", "Batch_number", "Unit_price", "subtotal"):
        shop_tree.heading(col, text=col)
        shop_tree.column(col, anchor=tk.CENTER)

    # ───── Buttons Frame ─────
    btn_frame = tk.Frame(buy_win, bg="lightgreen")
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="View_Daily_Sales", command=view_daily_sales, width=15).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="Add to List", command=add_item, width=15).grid(row=0, column=1, padx=5)
    tk.Button(btn_frame, text="Delete Item", command=delete_item, width=15).grid(row=0, column=2, padx=5)
    tk.Button(btn_frame, text="Total Price", command=show_total, width=15).grid(row=0, column=3, padx=5)
    tk.Button(btn_frame, text="Exit", command=exit_window, width=15).grid(row=0, column=7, padx=5)
    tk.Button(btn_frame, text="Print Receipt", command=print_receipt, width=15).grid(row=0, column=6, padx=5)

    tk.Label(btn_frame, text="G.Total:", bg="lightgreen", font=("Arial", 12)).grid(row=0,column=4, padx=5)
    tk.Entry(btn_frame, textvariable=total_var, state="readonly", width=15).grid(row=0, column=5, padx=5)

    load_stock()
root = tk.Tk()
root.title("Quick Service Supermarket Login")
root.geometry("800x600")
root.configure(bg="purple")

setup_database()
load_logo(root)
tk.Label(root, text="Please Login", font=("Arial", 24, "bold"), fg="white", bg="purple").pack(pady=10)

tk.Label(root, text="Username:", bg="purple", fg="white").pack()
username_entry = tk.Entry(root, font=("Arial", 14))
username_entry.pack()

tk.Label(root, text="Password:", bg="purple", fg="white").pack()
password_entry = tk.Entry(root, show="*", font=("Arial", 14))
password_entry.pack()

tk.Button(root, text="Login", font=("Arial", 14), command=login).pack(pady=10)
tk.Button(root, text="Register", font=("Arial", 12), command=open_registration).pack()
tk.Button(root, text="Exit", bg="red", fg="white", command=lambda: (root.destroy())).pack(pady=5)  
username_entry.focus()
root.bind('<Return>', lambda e: login())

root.mainloop()     