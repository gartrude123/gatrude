import tkinter as tk
from tkinter import messagebox
import sqlite3
import hashlib
from PIL import Image, ImageTk
import requests
from io import BytesIO
import os
import sys

# Setup paths
db_path = "supermarket.db"
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ---------- UTILITY ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def restart_app():
    root.destroy()
    os.execl(sys.executable, sys.executable, *sys.argv)

# ---------- DATABASE SETUP ----------
def setup_database():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS app_state (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quantity INTEGER,
        name TEXT,
        unit_price REALF
    )''')
    # Ensure admin exists
    if not c.execute("SELECT * FROM users WHERE username='admin'").fetchone():
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  ("admin", hash_password("password123")))
    if not c.execute("SELECT * FROM app_state WHERE key='admin_logged_in'").fetchone():
        c.execute("INSERT INTO app_state (key, value) VALUES ('admin_logged_in', 'no')")
    conn.commit()
    conn.close()

# ---------- LOGO ----------
def load_logo(parent):
    try:
        url = "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Shopping_cart_icon.svg/1024px-Shopping_cart_icon.svg.png"
        img_data = requests.get(url).content
        img = Image.open(BytesIO(img_data)).resize((80, 80))
        logo = ImageTk.PhotoImage(img)
        label = tk.Label(parent, image=logo, bg=parent["bg"])
        label.image = logo
        label.pack(pady=5)
    except:
        tk.Label(parent, text="SHOP LOGO", font=("Arial", 14), bg=parent["bg"]).pack(pady=5)

# ---------- LOGIN ----------
def login():
    user = username_entry.get().strip()
    pwd = password_entry.get().strip()
    hashed = hash_password(pwd)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    admin_logged = c.execute("SELECT value FROM app_state WHERE key='admin_logged_in'").fetchone()[0]

    if user == "admin":
        if hashed == hash_password("password123"):
            c.execute("UPDATE app_state SET value='yes' WHERE key='admin_logged_in'")
            conn.commit()
            conn.close()
            show_welcome_screen(user)
            return
        else:
            messagebox.showerror("Login Failed", "Incorrect admin password")
            return

    if admin_logged != "yes":
        messagebox.showerror("Access Denied", "Admin must log in first.")
        return

    c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, hashed))
    if c.fetchone():
        conn.close()
        show_welcome_screen(user)
    else:
        messagebox.showerror("Login Failed", "Incorrect credentials.")
        password_entry.delete(0, tk.END)

# ---------- REGISTER ----------
def open_registration():
    def register():
        user = reg_username.get()
        pwd = reg_password.get()
        if not user or not pwd:
            messagebox.showerror("Input Error", "Fill in all fields.")
            return
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                      (user, hash_password(pwd)))
            conn.commit()
            reg_win.destroy()
            messagebox.showinfo("Success", "User registered.")
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
    tk.Button(reg_win, text="Register", command=register).pack(pady=20)

# ---------- WELCOME ----------
def show_welcome_screen(username):
    for widget in root.winfo_children():
        widget.destroy()
    root.configure(bg="orange")
    load_logo(root)

    tk.Label(root, text=f"Welcome {username}", font=("Arial", 24, "bold"), bg="orange").pack(pady=20)

    tk.Button(root, text="View Stock", font=("Arial", 16), width=20, command=lambda: view_stock_window(username)).pack(pady=10)
    tk.Button(root, text="Logout", font=("Arial", 14), bg="red", fg="white", command=restart_app).pack(pady=40)
    tk.Button(root, text="Buy Item", font=("Arial", 16), width=20, command=lambda: buy_item_window(username)).pack(pady=10)

# ---------- STOCK WINDOW ----------
import tkinter.ttk as ttk  # Add this import if it's not in your code

def view_stock_window(username):
    stock_win = tk.Toplevel(root)
    stock_win.title("Supermarket Stock")
    stock_win.geometry("850x600")
    stock_win.configure(bg="lightyellow")
    load_logo(stock_win)

    tk.Label(stock_win, text="WELCOME TO OUR STOCK", font=("Arial", 22, "bold"), bg="lightyellow").pack(pady=10)

    # Frame for the Treeview
    frame = tk.Frame(stock_win, bg="lightyellow")
    frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

    # Scrollbar
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Treeview for table
    tree = ttk.Treeview(frame, columns=("Quantity", "Description", "Unit Price"), show='headings', yscrollcommand=scrollbar.set, height=20)
    tree.heading("Quantity", text="Quantity")
    tree.heading("Description", text="Description")
    tree.heading("Unit Price", text="Unit Price (UGX)")
    tree.column("Quantity", width=100, anchor=tk.CENTER)
    tree.column("Description", width=300)
    tree.column("Unit Price", width=150, anchor=tk.E)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=tree.yview)

    def load_stock():
        tree.delete(*tree.get_children())
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        for row in c.execute("SELECT id, quantity, name, unit_price FROM stock"):
            tree.insert("", tk.END, iid=row[0], values=(row[1], row[2], f"{row[3]:,.0f}"))
        conn.close()

    def add_item():
        popup = tk.Toplevel(stock_win)
        popup.title("Add Stock")
        popup.geometry("300x250")
        popup.configure(bg="lightblue")

        tk.Label(popup, text="Quantity", bg="lightblue").pack()
        qty_entry = tk.Entry(popup)
        qty_entry.pack()
        tk.Label(popup, text="Name", bg="lightblue").pack()
        name_entry = tk.Entry(popup)
        name_entry.pack()
        tk.Label(popup, text="Unit Price", bg="lightblue").pack()
        price_entry = tk.Entry(popup)
        price_entry.pack()

        def save():
            try:
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute("INSERT INTO stock (quantity, name, unit_price) VALUES (?, ?, ?)",
                          (int(qty_entry.get()), name_entry.get(), float(price_entry.get())))
                conn.commit()
                conn.close()
                popup.destroy()
                load_stock()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {e}")

        tk.Button(popup, text="Save", command=save).pack(pady=10)

    def delete_item():
        selected = tree.selection()
        if not selected:
            return
        item_id = selected[0]
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("DELETE FROM stock WHERE id=?", (item_id,))
        conn.commit()
        conn.close()
        load_stock()

    def increase_quantity():
        selected = tree.selection()
        if not selected:
            return
        item_id = selected[0]

        popup = tk.Toplevel(stock_win)
        popup.title("Increase Quantity")
        popup.geometry("250x150")
        popup.configure(bg="lightblue")

        tk.Label(popup, text="Additional Quantity:", bg="lightblue").pack()
        qty_entry = tk.Entry(popup)
        qty_entry.pack()

        def update_qty():
            try:
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute("UPDATE stock SET quantity = quantity + ? WHERE id = ?",
                          (int(qty_entry.get()), item_id))
                conn.commit()
                conn.close()
                popup.destroy()
                load_stock()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {e}")

        tk.Button(popup, text="Update", command=update_qty).pack(pady=10)
    def increase_price():
        selected = tree.selection()
        if not selected:
            return
        item_id = selected[0]

        popup = tk.Toplevel(stock_win)
        popup.title("Increase Unit Price")
        popup.geometry("250x150")
        popup.configure(bg="lightblue")

        tk.Label(popup, text="Amount to Increase (UGX):", bg="lightblue").pack(pady=5)
        price_entry = tk.Entry(popup)
        price_entry.pack()

        def update_price():
            try:
                increment = float(price_entry.get())
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute("UPDATE stock SET unit_price = unit_price + ? WHERE id = ?", (increment, item_id))
                conn.commit()
                conn.close()
                popup.destroy()
                load_stock()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {e}")

        tk.Button(popup, text="Update Price", command=update_price).pack(pady=10)
    

    # Menu frame for buttons
    menu_frame = tk.Frame(stock_win, bg="lightyellow")
    menu_frame.pack(pady=10)

    tk.Button(menu_frame, text="Add Item", command=add_item).grid(row=0, column=0, padx=10)
    tk.Button(menu_frame, text="Delete Selected", command=delete_item).grid(row=0, column=1, padx=10)
    tk.Button(menu_frame, text="Increase Quantity", command=increase_quantity).grid(row=0, column=2, padx=10)
    tk.Button(menu_frame, text="Increase Price", command=increase_price).grid(row=0, column=3, padx=10)
    tk.Button(menu_frame, text="Exit to Welcome", bg="red", fg="white", command=stock_win.destroy).grid(row=0, column=4, padx=10)

    load_stock()
def buy_item_window(username):
    buy_win = tk.Toplevel(root)
    buy_win.title("Buy Items")
    buy_win.geometry("900x650")
    buy_win.configure(bg="lightgreen")
    load_logo(buy_win)

    tk.Label(buy_win, text="BUY ITEMS", font=("Arial", 22, "bold"), bg="lightgreen").pack(pady=10)

    frame = tk.Frame(buy_win)
    frame.pack(fill=tk.BOTH, expand=True, padx=10)

    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    tree = ttk.Treeview(frame, columns=("Quantity", "Description", "Unit Price"), show="headings", yscrollcommand=scrollbar.set)
    tree.heading("Quantity", text="QNTY")
    tree.heading("Description", text="ITEM DESCRIPTION")
    tree.heading("Unit Price", text="UNIT PRICE (UGX)")
    tree.column("Quantity", width=80, anchor=tk.CENTER)
    tree.column("Description", width=350)
    tree.column("Unit Price", width=150, anchor=tk.E)
    tree.pack(fill=tk.BOTH, expand=True)
    scrollbar.config(command=tree.yview)

    shopping_list = []

    def load_items():
        tree.delete(*tree.get_children())
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        for row in c.execute("SELECT id, quantity, name, unit_price FROM stock"):
            tree.insert("", tk.END, iid=row[0], values=(row[1], row[2], f"{row[3]:,.0f}"))
        conn.close()

    def add_to_list():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Select Item", "Please select an item to add.")
            return
        item_id = selected[0]
        quantity, description, price = tree.item(item_id, "values")

        qty_win = tk.Toplevel(buy_win)
        qty_win.title("Select Quantity")
        qty_win.geometry("250x150")
        qty_win.configure(bg="lightblue")

        tk.Label(qty_win, text=f"Enter quantity to buy (Available: {quantity}):", bg="lightblue").pack(pady=5)
        qty_entry = tk.Entry(qty_win)
        qty_entry.pack()

        def confirm_add():
            try:
                qty_to_buy = int(qty_entry.get())
                if qty_to_buy <= 0 or qty_to_buy > int(quantity):
                    raise ValueError("Invalid quantity")

                price_total = qty_to_buy * float(price.replace(',', ''))
                shopping_list.append((description, qty_to_buy, price_total))
                listbox.insert(tk.END, f"{description} x{qty_to_buy} - UGX {price_total:,.0f}")
                update_total()
                qty_win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {e}")

        tk.Button(qty_win, text="Add", command=confirm_add).pack(pady=10)

    def remove_from_list():
        selected = listbox.curselection()
        if not selected:
            return
        index = selected[0]
        del shopping_list[index]
        listbox.delete(index)
        update_total()

    def update_total():
        total = sum(price for _, _, price in shopping_list)
        total_var.set(f"{total:,.0f}")

    def print_receipt():
        if not shopping_list:
            messagebox.showwarning("No Items", "No items to print.")
            return

        # Check printer connection (simulated check)
        try:
            # This simulates trying to use the printer
            # On real printers, you'd use OS or printer API checks
            test_file = "receipt_test.txt"
            with open(test_file, "w") as f:
                f.write("Printer test.")
            os.startfile(test_file, "print")
            os.remove(test_file)
        except Exception:
            messagebox.showinfo("Printer", "Please connect to the printer to print receipt.")
            return

        receipt = "----- QUICK SERVICE SUPERMARKET RECEIPT -----\n\n"
        for name, qty, price in shopping_list:
            receipt += f"{name:<25} x{qty:<3} UGX {price:,.0f}\n"
        receipt += "\n" + "-" * 45
        total = sum(price for _, _, price in shopping_list)
        receipt += f"\nTOTAL: UGX {total:,.0f}"
        receipt += "\n\nSeller Signature: __________________\n"

        filename = "receipt.txt"
        with open(filename, "w") as f:
            f.write(receipt)

        try:
            os.startfile(filename, "print")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to print receipt: {e}")

    def close_window():
        buy_win.destroy()
        buy_item_window(username)

    # Shopping list section
    tk.Label(buy_win, text="Shopping List", font=("Arial", 14), bg="lightgreen").pack()
    listbox = tk.Listbox(buy_win, font=("Arial", 12), width=70, height=6)
    listbox.pack()

    btn_frame = tk.Frame(buy_win, bg="lightgreen")
    btn_frame.pack(pady=5)
    tk.Button(btn_frame, text="Add to List", command=add_to_list).grid(row=0, column=0, padx=10)
    tk.Button(btn_frame, text="Remove Selected", command=remove_from_list).grid(row=0, column=1, padx=10)

    # Total section
    total_var = tk.StringVar(value="0")
    total_frame = tk.Frame(buy_win, bg="lightgreen")
    total_frame.pack(pady=10)
    tk.Label(total_frame, text="Total: UGX", font=("Arial", 14), bg="lightgreen").grid(row=0, column=0)
    tk.Entry(total_frame, textvariable=total_var, font=("Arial", 14), state="readonly", width=15).grid(row=0, column=1, padx=5)
    tk.Button(total_frame, text="Total", command=update_total).grid(row=0, column=2, padx=10)

    # Print and exit
    bottom_frame = tk.Frame(buy_win, bg="lightgreen")
    bottom_frame.pack(pady=20)
    tk.Button(bottom_frame, text="Print Receipt", command=print_receipt).grid(row=0, column=0, padx=20)
    tk.Button(bottom_frame, text="Exit", bg="red", fg="white", command=close_window).grid(row=0, column=1, padx=20)

    load_items()

# ---------- GUI ----------
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

username_entry.focus()
root.bind('<Return>', lambda e: login())

root.mainloop()
