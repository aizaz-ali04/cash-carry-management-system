import tkinter as tk
from tkinter import messagebox, ttk
import json, os
from datetime import datetime

# FILES & FOLDERS
PRODUCTS_FILE  = "products.json"
SALES_FILE     = "sales.json"
RECEIPTS_FOLDER = "receipts"

os.makedirs(RECEIPTS_FOLDER, exist_ok=True)

# COLORS 
BG       = "#f5f6fa"
WHITE    = "#ffffff"
GREEN    = "#27ae60"
RED      = "#e74c3c"
BLUE     = "#2980b9"
ORANGE   = "#e67e22"
PURPLE   = "#8e44ad"
GRAY     = "#95a5a6"
DARK     = "#2c3e50"
LIGHT    = "#ecf0f1"

#  STATE 
cart  = {}
total = 0

#  DATA HELPERS

def load_products():
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE) as f:
            return json.load(f)
    return []

def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=4)

def load_sales():
    if os.path.exists(SALES_FILE):
        with open(SALES_FILE) as f:
            return json.load(f)
    return []

def save_sales(sales):
    with open(SALES_FILE, "w") as f:
        json.dump(sales, f, indent=4)

#  RECEIPT

def show_receipt(cart_data, sale_total):
    pop = tk.Toplevel(window)
    pop.title("Receipt")
    pop.config(bg=WHITE)
    pop.resizable(True, True)

    # size: fit screen height, cap at 600px tall
    screen_h = pop.winfo_screenheight()
    win_h    = min(600, int(screen_h * 0.85))
    pop.geometry(f"380x{win_h}")

    tk.Label(pop, text="CASH & CARRY", font=("Courier", 14, "bold"),
             bg=WHITE).pack(pady=(12, 2))
    now = datetime.now().strftime("%d-%m-%Y  %H:%M")
    tk.Label(pop, text=now, font=("Courier", 9), fg=GRAY, bg=WHITE).pack()

    # Text with scrollbar so long receipts don't overflow
    txt_frame = tk.Frame(pop, bg=WHITE)
    txt_frame.pack(fill="both", expand=True, padx=15, pady=8)

    txt_sb = tk.Scrollbar(txt_frame)
    txt_sb.pack(side="right", fill="y")

    txt = tk.Text(txt_frame, font=("Courier", 10), bg=LIGHT, bd=0,
                  relief="flat", padx=10, pady=8,
                  yscrollcommand=txt_sb.set)
    txt.pack(side="left", fill="both", expand=True)
    txt_sb.config(command=txt.yview)

    lines  = "-" * 38 + "\n"
    lines += f"{'Item':<20}{'Qty':>5}{'Total':>10}\n"
    lines += "-" * 38 + "\n"
    for name, d in cart_data.items():
        item_total = d["price"] * d["qty"]
        lines += f"{name[:20]:<20}{d['qty']:>5}{item_total:>10.0f}\n"
    lines += "-" * 38 + "\n"
    lines += f"{'TOTAL':>28}   Rs {sale_total:.0f}\n"
    lines += "-" * 38 + "\n"
    lines += "\n      Thank you for shopping!\n"
    txt.insert("end", lines)
    txt.config(state="disabled")

    # save to file
    fname = os.path.join(RECEIPTS_FOLDER,
                         f"receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(fname, "w") as f:
        f.write(f"CASH & CARRY\n{now}\n\n{lines}")

    def try_print():
        try:
            os.startfile(fname, "print")
        except Exception:
            msg("Printer not available", "orange")

    btn_row = tk.Frame(pop, bg=WHITE)
    btn_row.pack(pady=(0, 12))
    tk.Button(btn_row, text="🖨  Print",  command=try_print,
              bg=GREEN, fg=WHITE, padx=14, pady=5).pack(side="left", padx=6)
    tk.Button(btn_row, text="✕  Close", command=pop.destroy,
              bg=RED,   fg=WHITE, padx=14, pady=5).pack(side="left", padx=6)

#  STATUS MESSAGE

def msg(text, color="green"):
    msg_label.config(text=text, fg=color)
    window.after(3000, lambda: msg_label.config(text=""))

#  ADD / EDIT PRODUCT

def add_product():
    name  = entry_name.get().strip()
    price = entry_price.get().strip()
    qty   = entry_qty.get().strip()
    cat   = category_var.get().strip()

    if not name or not price or not qty:
        msg("Fill all fields!", "red"); return

    try:
        price_f = float(price)
        qty_i   = int(qty)
        if price_f < 0 or qty_i < 0:
            raise ValueError
    except ValueError:
        msg("Price and Qty must be valid numbers!", "red"); return

    products = load_products()

    # if same name exists → update qty instead of duplicate
    for p in products:
        if p["name"].lower() == name.lower():
            p["quantity"] += qty_i
            save_products(products)
            msg(f"Updated stock for '{name}'", "blue")
            _clear_add_form()
            show_products()
            return

    products.append({
        "name":     name,
        "price":    price_f,
        "quantity": qty_i,
        "category": cat
    })
    save_products(products)
    msg(f"'{name}' saved!", GREEN)
    _clear_add_form()
    show_products()

def _clear_add_form():
    entry_name.delete(0, tk.END)
    entry_price.delete(0, tk.END)
    entry_qty.delete(0, tk.END)
    category_var.set("General")

def delete_product(name):
    if not messagebox.askyesno("Delete", f"Delete '{name}'?"):
        return
    products = [p for p in load_products() if p["name"] != name]
    # also remove from cart
    if name in cart:
        global total
        total -= cart[name]["price"] * cart[name]["qty"]
        del cart[name]
        update_cart()
    save_products(products)
    msg(f"'{name}' deleted.", GRAY)
    show_products()

def open_edit_window(product):
    pop = tk.Toplevel(window)
    pop.title(f"Edit — {product['name']}")
    pop.geometry("320x260")
    pop.config(bg=BG)
    pop.resizable(False, False)

    fields = [("Name",  product["name"]),
              ("Price", product["price"]),
              ("Qty",   product["quantity"])]
    entries = {}

    for i, (lbl, val) in enumerate(fields):
        tk.Label(pop, text=lbl, bg=BG, font=("Arial", 10)).grid(
            row=i, column=0, padx=15, pady=8, sticky="w")
        e = tk.Entry(pop, width=20)
        e.insert(0, str(val))
        e.grid(row=i, column=1, padx=10)
        entries[lbl] = e

    # category
    tk.Label(pop, text="Category", bg=BG, font=("Arial", 10)).grid(
        row=3, column=0, padx=15, pady=8, sticky="w")
    cat_var = tk.StringVar(value=product.get("category", "General"))
    cat_menu = ttk.Combobox(pop, textvariable=cat_var,
                            values=["General","Food","Drinks","Household","Other"],
                            width=18, state="readonly")
    cat_menu.grid(row=3, column=1, padx=10)

    def save_edit():
        products = load_products()
        for p in products:
            if p["name"] == product["name"]:
                try:
                    p["name"]     = entries["Name"].get().strip()
                    p["price"]    = float(entries["Price"].get())
                    p["quantity"] = int(entries["Qty"].get())
                    p["category"] = cat_var.get()
                except ValueError:
                    msg("Invalid values!", "red"); return
        save_products(products)
        msg("Product updated!", BLUE)
        pop.destroy()
        show_products()

    btn_row = tk.Frame(pop, bg=BG)
    btn_row.grid(row=4, column=0, columnspan=2, pady=12)
    tk.Button(btn_row, text="Save",   command=save_edit,  bg=BLUE,  fg=WHITE, padx=16).pack(side="left", padx=6)
    tk.Button(btn_row, text="Cancel", command=pop.destroy, bg=GRAY,  fg=WHITE, padx=12).pack(side="left")

#  SHOW PRODUCTS

def show_products():
    for w in products_frame.winfo_children():
        w.destroy()

    search   = search_entry.get().lower()
    cat_f    = filter_var.get()
    products = load_products()

    shown = [p for p in products
             if search in p["name"].lower()
             and (cat_f == "All" or p.get("category","General") == cat_f)]

    if not shown:
        tk.Label(products_frame, text="No products found.",
                 fg=GRAY, bg=WHITE, font=("Arial", 10)).pack(pady=12)
        return

    for i, p in enumerate(shown):
        row_bg = WHITE if i % 2 == 0 else "#f8f9fa"
        row = tk.Frame(products_frame, bg=row_bg, pady=4)
        row.pack(fill="x", padx=4)

        # icon
        tk.Label(row, text="📦", font=("Arial", 22),
                 bg=row_bg).pack(side="left", padx=6, pady=2)

        # info
        info_col = tk.Frame(row, bg=row_bg)
        info_col.pack(side="left", fill="x", expand=True, padx=4)

        name_fg = RED if p["quantity"] == 0 else DARK
        tk.Label(info_col, text=p["name"], font=("Arial", 10, "bold"),
                 fg=name_fg, bg=row_bg, anchor="w").pack(anchor="w")

        stock_fg = RED if p["quantity"] == 0 else (ORANGE if p["quantity"] <= 5 else GREEN)
        stock_txt = "Out of Stock" if p["quantity"] == 0 else f"Stock: {p['quantity']}"
        tk.Label(info_col,
                 text=f"Rs {p['price']:.0f}  |  {stock_txt}  |  {p.get('category','General')}",
                 font=("Arial", 9), fg=stock_fg, bg=row_bg, anchor="w").pack(anchor="w")

        # buttons
        btn_col = tk.Frame(row, bg=row_bg)
        btn_col.pack(side="right", padx=6)

        if p["quantity"] > 0:
            tk.Button(btn_col, text="＋ Add",
                      command=lambda prod=p: add_to_cart(prod),
                      bg=GREEN, fg=WHITE, font=("Arial", 9),
                      padx=8, pady=2).pack(side="left", padx=3)

        tk.Button(btn_col, text="✏",
                  command=lambda prod=p: open_edit_window(prod),
                  bg=BLUE, fg=WHITE, padx=6, pady=2).pack(side="left", padx=2)

        tk.Button(btn_col, text="🗑",
                  command=lambda n=p["name"]: delete_product(n),
                  bg=RED, fg=WHITE, padx=6, pady=2).pack(side="left", padx=2)

#  CART

def add_to_cart(product):
    global total
    products = load_products()
    for p in products:
        if p["name"] == product["name"]:
            if p["quantity"] <= 0:
                msg("Out of stock!", "red"); return
            p["quantity"] -= 1
            break
    save_products(products)

    name = product["name"]
    cart[name] = cart.get(name, {"price": product["price"], "qty": 0})
    cart[name]["qty"] += 1
    total += product["price"]
    show_products()
    update_cart()
    msg(f"Added '{name}'", GREEN)

def remove_one(name):
    global total
    if name not in cart: return
    products = load_products()
    for p in products:
        if p["name"] == name:
            p["quantity"] += 1
            break
    save_products(products)
    total -= cart[name]["price"]
    cart[name]["qty"] -= 1
    if cart[name]["qty"] == 0:
        del cart[name]
    show_products()
    update_cart()

def remove_all_of(name):
    global total
    if name not in cart: return
    products = load_products()
    for p in products:
        if p["name"] == name:
            p["quantity"] += cart[name]["qty"]
            break
    save_products(products)
    total -= cart[name]["price"] * cart[name]["qty"]
    del cart[name]
    show_products()
    update_cart()

def update_cart():
    for w in cart_frame.winfo_children():
        w.destroy()

    if not cart:
        tk.Label(cart_frame, text="Cart is empty",
                 fg=GRAY, bg=BG, font=("Arial", 10)).pack(pady=8)
    else:
        for i, (name, data) in enumerate(cart.items()):
            row_bg = WHITE if i % 2 == 0 else LIGHT
            row = tk.Frame(cart_frame, bg=row_bg)
            row.pack(fill="x", pady=1, padx=4)

            line = f"{name[:24]}   x{data['qty']}   =   Rs {data['price']*data['qty']:.0f}"
            tk.Label(row, text=line, bg=row_bg,
                     font=("Arial", 9), anchor="w", width=36).pack(side="left", padx=6, pady=4)

            tk.Button(row, text="−",
                      command=lambda n=name: remove_one(n),
                      bg=ORANGE, fg=WHITE, padx=6, pady=1,
                      font=("Arial", 10, "bold")).pack(side="right", padx=2, pady=3)
            tk.Button(row, text="✕",
                      command=lambda n=name: remove_all_of(n),
                      bg=RED, fg=WHITE, padx=6, pady=1,
                      font=("Arial", 10, "bold")).pack(side="right", padx=2)

    item_count = sum(d["qty"] for d in cart.values())
    total_label.config(text=f"Items: {item_count}   |   Total:  Rs {total:.0f}")

def checkout():
    global cart, total
    if not cart:
        msg("Cart is empty!", "red"); return

    if not messagebox.askyesno("Checkout",
            f"Confirm sale?\nTotal: Rs {total:.0f}"):
        return

    sales = load_sales()
    sales.append({
        "date":  datetime.now().strftime("%Y-%m-%d %H:%M"),
        "items": {k: v.copy() for k, v in cart.items()},
        "total": round(total, 2)
    })
    save_sales(sales)

    show_receipt(cart, total)
    msg(f"✔ Sale done! Rs {total:.0f} received.", GREEN)
    cart  = {}
    total = 0
    update_cart()

def clear_cart():
    global cart, total
    if not cart: return
    if not messagebox.askyesno("Clear Cart", "Remove all items?"):
        return
    products = load_products()
    for name, data in cart.items():
        for p in products:
            if p["name"] == name:
                p["quantity"] += data["qty"]; break
    save_products(products)
    cart  = {}
    total = 0
    show_products()
    update_cart()

#  SALES HISTORY WINDOW

def open_sales_window():
    pop = tk.Toplevel(window)
    pop.title("Sales History")
    pop.geometry("520x420")
    pop.config(bg=BG)

    tk.Label(pop, text="Sales History", font=("Arial", 13, "bold"),
             bg=BG).pack(pady=(12, 4))

    cols = ("Date", "Items", "Total (Rs)")
    tree = ttk.Treeview(pop, columns=cols, show="headings", height=14)
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=160)
    tree.pack(fill="both", expand=True, padx=15, pady=8)

    sales = load_sales()
    revenue = 0
    for s in reversed(sales):
        n_items = sum(d["qty"] for d in s["items"].values())
        tree.insert("", "end",
                    values=(s.get("date","—"), n_items, f"Rs {s['total']:.0f}"))
        revenue += s["total"]

    summary = tk.Frame(pop, bg=BG)
    summary.pack(fill="x", padx=15, pady=(0, 10))
    tk.Label(summary, text=f"Total sales: {len(sales)}",
             font=("Arial", 10, "bold"), bg=BG, fg=DARK).pack(side="left")
    tk.Label(summary, text=f"Total revenue: Rs {revenue:.0f}",
             font=("Arial", 10, "bold"), bg=BG, fg=GREEN).pack(side="right")

#  WINDOW  &  UI

window = tk.Tk()
window.title("Cash & Carry System")
window.geometry("760x700")
window.config(bg=BG)
window.resizable(True, True)

# Top bar 
topbar = tk.Frame(window, bg=DARK, height=50)
topbar.pack(fill="x")
topbar.pack_propagate(False)

tk.Label(topbar, text="🛒  Cash & Carry System",
         font=("Arial", 14, "bold"), bg=DARK, fg=WHITE).pack(side="left", padx=18, pady=10)

tk.Button(topbar, text="📊 Sales History", command=open_sales_window,
          bg=PURPLE, fg=WHITE, padx=10, pady=4,
          relief="flat", cursor="hand2").pack(side="right", padx=12, pady=8)

msg_label = tk.Label(topbar, text="", font=("Arial", 9),
                     bg=DARK, fg=GREEN)
msg_label.pack(side="right", padx=10)

# Add Product panel 
add_frame = tk.LabelFrame(window, text="  Add / Update Product  ",
                           bg=BG, font=("Arial", 10, "bold"), padx=8, pady=8)
add_frame.pack(fill="x", padx=14, pady=(10, 4))

# row 0: Name, Price, Qty
tk.Label(add_frame, text="Name",  bg=BG).grid(row=0, column=0, padx=4, pady=3, sticky="w")
entry_name  = tk.Entry(add_frame, width=15); entry_name.grid(row=0, column=1, padx=4)

tk.Label(add_frame, text="Price", bg=BG).grid(row=0, column=2, padx=4, sticky="w")
entry_price = tk.Entry(add_frame, width=9);  entry_price.grid(row=0, column=3, padx=4)

tk.Label(add_frame, text="Qty",   bg=BG).grid(row=0, column=4, padx=4, sticky="w")
entry_qty   = tk.Entry(add_frame, width=7);  entry_qty.grid(row=0, column=5, padx=4)

# row 1: Category, Save
tk.Label(add_frame, text="Category", bg=BG).grid(row=1, column=0, padx=4, pady=4, sticky="w")
category_var = tk.StringVar(value="General")
cat_menu = ttk.Combobox(add_frame, textvariable=category_var,
                        values=["General","Food","Drinks","Household","Other"],
                        width=12, state="readonly")
cat_menu.grid(row=1, column=1, padx=4)

tk.Button(add_frame, text="💾 Save", command=add_product,
          bg=BLUE, fg=WHITE, padx=14, pady=3).grid(row=1, column=2, padx=6, columnspan=2)

# Search & filter
search_bar = tk.Frame(window, bg=BG)
search_bar.pack(fill="x", padx=14, pady=4)

tk.Label(search_bar, text="Search:", bg=BG).pack(side="left")
search_entry = tk.Entry(search_bar, width=22)
search_entry.pack(side="left", padx=5)
search_entry.bind("<KeyRelease>", lambda e: show_products())

tk.Label(search_bar, text="Category:", bg=BG).pack(side="left", padx=(10, 2))
filter_var = tk.StringVar(value="All")
filter_menu = ttk.Combobox(search_bar, textvariable=filter_var,
                            values=["All","General","Food","Drinks","Household","Other"],
                            width=11, state="readonly")
filter_menu.pack(side="left")
filter_menu.bind("<<ComboboxSelected>>", lambda e: show_products())

tk.Button(search_bar, text="🔍 Search", command=show_products,
          bg=DARK, fg=WHITE, padx=8).pack(side="left", padx=6)

# Products list (scrollable)
tk.Label(window, text="Products", font=("Arial", 10, "bold"),
         bg=BG, anchor="w").pack(fill="x", padx=16)

prod_outer = tk.Frame(window, bg=WHITE, relief="sunken", bd=1)
prod_outer.pack(fill="x", padx=14, pady=4)

prod_canvas = tk.Canvas(prod_outer, bg=WHITE, height=220, highlightthickness=0)
prod_sb     = tk.Scrollbar(prod_outer, orient="vertical", command=prod_canvas.yview)
prod_canvas.configure(yscrollcommand=prod_sb.set)
prod_sb.pack(side="right", fill="y")
prod_canvas.pack(side="left", fill="both", expand=True)

products_frame = tk.Frame(prod_canvas, bg=WHITE)
prod_canvas.create_window((0, 0), window=products_frame, anchor="nw")
products_frame.bind("<Configure>",
    lambda e: prod_canvas.configure(scrollregion=prod_canvas.bbox("all")))
prod_canvas.bind_all("<MouseWheel>",
    lambda e: prod_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

# Cart
tk.Label(window, text="Cart", font=("Arial", 10, "bold"),
         bg=BG, anchor="w").pack(fill="x", padx=16, pady=(6, 0))

cart_frame = tk.Frame(window, bg=BG, relief="sunken", bd=1)
cart_frame.pack(fill="both", expand=True, padx=14, pady=4)

# Bottom bar
bottom = tk.Frame(window, bg=DARK, height=48)
bottom.pack(fill="x", side="bottom")
bottom.pack_propagate(False)

total_label = tk.Label(bottom, text="Items: 0   |   Total:  Rs 0",
                       font=("Arial", 11, "bold"), bg=DARK, fg=WHITE)
total_label.pack(side="left", padx=16, pady=10)

tk.Button(bottom, text="✔ Checkout",  command=checkout,
          bg=GREEN, fg=WHITE, font=("Arial", 10, "bold"),
          padx=14, pady=4, relief="flat", cursor="hand2").pack(side="right", padx=10, pady=8)

tk.Button(bottom, text="🗑 Clear Cart", command=clear_cart,
          bg=RED, fg=WHITE, padx=10, pady=4,
          relief="flat", cursor="hand2").pack(side="right", pady=8)

#  launch
show_products()
update_cart()
window.mainloop()