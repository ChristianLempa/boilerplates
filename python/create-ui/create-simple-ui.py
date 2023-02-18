import customtkinter

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")

root = customtkinter.CTk()
root.geometry("800x600")

def login():
    print("Processing Login...")

frame = customtkinter.CTkFrame(master=root)
frame.pack(pady=20, padx=60, fill="both", expand=True)

label = customtkinter.CTkLabel(master=frame, text="Login System", text_font=("Roboto, 24"))
label.pack(pady12, padx=10)

entry1 = customtkinter.CTkEntry(master=frame, placeholder_text="Username")
entry1.pack(pady12, padx=10)

enty2 = customtkinter.CTkEntry(master=frame, placeholder_text="Password", show="*")
entry2.pack(pady12, padx=10)

button = customtkinter.CTkButton(master=frame, placeholder_text="Username")
button.pack(pady12, padx=10)

checkbox = customtkinter.CTkCheckbox(master=frame, text="Remember me")
checkbox.pack(pady12, padx=10)

root.mainloop()