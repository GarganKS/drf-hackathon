import tkinter as tk
from tkinter import messagebox


PASSWORD = "1111"


def check_password(event=None):
    if password_entry.get() == PASSWORD:
        root.destroy()
    else:
        message_label.config(
            text="Неправильний пароль! Спробуй ще раз."
        )
        password_entry.delete(0, tk.END)


def exit_locker():
    if messagebox.askyesno(
        "Вихід",
        "Точно хочеш вийти з вінлокера?"
    ):
        root.destroy()


root = tk.Tk()

root.title("Funny Locker")
root.attributes("-fullscreen", True)
root.configure(bg="#111111")

root.bind("<Escape>", lambda event: exit_locker())

main_frame = tk.Frame(root, bg="#111111")
main_frame.place(relx=0.5, rely=0.5, anchor="center")

title = tk.Label(
    main_frame,
    text="ТВОЄГО ПК ЗАХОПЛЕНО!",
    font=("Arial", 32, "bold"),
    fg="#ff4444",
    bg="#111111"
)
title.pack(pady=20)

description = tk.Label(
    main_frame,
    text="Введи пароль, щоб повернути контроль.",
    font=("Arial", 16),
    fg="white",
    bg="#111111"
)
description.pack(pady=10)

password_entry = tk.Entry(
    main_frame,
    font=("Arial", 24),
    justify="center",
    show="*"
)
password_entry.pack(pady=15)

password_entry.bind("<Return>", check_password)

message_label = tk.Label(
    main_frame,
    text="",
    font=("Arial", 14),
    fg="#ff4444",
    bg="#111111"
)
message_label.pack(pady=10)

check_button = tk.Button(
    main_frame,
    text="Розблокувати",
    font=("Arial", 16),
    command=check_password
)
check_button.pack(pady=10)


root.mainloop()