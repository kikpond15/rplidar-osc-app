import tkinter as tk

root = tk.Tk()
root.title("Sanity Pack")
root.geometry("360x200")

lbl = tk.Label(root, text="Hello (pure Tk)", font=("Helvetica", 16))
lbl.pack(pady=20)
btn = tk.Button(root, text="Quit", command=root.destroy)
btn.pack()

def blink(i=[0]):
    root.configure(bg="#f0f0f0" if i[0]%2==0 else "#d0ffd0")
    i[0]+=1
    root.after(500, blink)
blink()

root.mainloop()
