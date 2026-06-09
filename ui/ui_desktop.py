import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from storage.db_manager import DatabaseManager
from utils.password_generator import generate_password
from utils.clipboard_manager import ClipboardManager


class VaultSelector(tk.Toplevel):
    """Dialog for selecting or creating a vault folder."""

    def __init__(self, parent, vaults_base: Path, existing_vaults: list[str]):
        super().__init__(parent)
        self.title("Select Vault")
        self.geometry("600x650")
        self.resizable(False, False)
        self.result = None
        self.vaults_base = vaults_base
        self.existing_vaults = existing_vaults

        self._build_ui()
        self.transient(parent)
        self.grab_set()

    def _build_ui(self) -> None:
        """Build the vault selection UI."""
        # Header
        header = ttk.Label(self, text="Select or Create a Vault", font=("Segoe UI", 14, "bold"))
        header.pack(fill="x", padx=20, pady=(20, 10))

        info = ttk.Label(
            self,
            text="Choose an existing vault or create a new one.",
            font=("Segoe UI", 9),
            foreground="#666666",
        )
        info.pack(fill="x", padx=20, pady=(0, 15))

        # Frame for existing vaults
        if self.existing_vaults:
            existing_label = ttk.Label(self, text="Existing Vaults:", font=("Segoe UI", 10, "bold"))
            existing_label.pack(fill="x", padx=20, pady=(10, 5))

            # Listbox with scrollbar
            list_frame = ttk.Frame(self)
            list_frame.pack(fill="both", expand=True, padx=10, pady=(5, 5))

            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")

            self.vault_listbox = tk.Listbox(
                list_frame,
                font=("Segoe UI", 10),
                yscrollcommand=scrollbar.set,
                height=8,
                relief="solid",
                borderwidth=1,
            )
            self.vault_listbox.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=self.vault_listbox.yview)

            for vault in self.existing_vaults:
                self.vault_listbox.insert(tk.END, vault)

            self.vault_listbox.bind("<Double-1>", lambda e: self._select_existing())

            # Button to select existing
            select_btn = ttk.Button(self, text="Open Selected Vault", command=self._select_existing)
            select_btn.pack(fill="x", padx=20, pady=(0, 25))

        # Separator
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=10)

        # New vault section
        new_label = ttk.Label(self, text="Create New Vault:", font=("Segoe UI", 10, "bold"))
        new_label.pack(fill="x", padx=20, pady=(10, 8))

        ttk.Label(self, text="Vault Name:", font=("Segoe UI", 9)).pack(fill="x", padx=20, pady=(0, 3))

        self.new_vault_entry = ttk.Entry(self, font=("Segoe UI", 10), width=40)
        self.new_vault_entry.pack(fill="x", padx=20, pady=(0, 12))
        self.new_vault_entry.focus()

        # Button frame for new vault
        new_btn = ttk.Button(self, text="Create New Vault", command=self._create_new)
        new_btn.pack(fill="x", padx=20, pady=(0, 15))

        # Cancel button
        cancel_btn = ttk.Button(self, text="Exit", command=self.destroy)
        cancel_btn.pack(fill="x", padx=20, pady=(0, 15))

    def _select_existing(self) -> None:
        """Select an existing vault from the listbox."""
        if not hasattr(self, "vault_listbox"):
            messagebox.showwarning("Selection Required", "No existing vaults.")
            return

        selection = self.vault_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Required", "Please select a vault from the list.")
            return

        self.result = self.vault_listbox.get(selection[0])
        self.destroy()

    def _create_new(self) -> None:
        """Create a new vault with the entered name."""
        name = self.new_vault_entry.get().strip()
        if not name:
            messagebox.showwarning("Input Required", "Please enter a vault name.")
            return

        self.result = name
        self.destroy()


class CredentialEditor(tk.Toplevel):
    """Modal dialog for creating or editing a credential."""

    def __init__(self, parent, title: str, credential: dict | None = None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self.credential = credential or {
            "website": "",
            "username": "",
            "password": "",
            "notes": "",
        }
        self._build_form()
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def _build_form(self) -> None:
        padding = {"padx": 10, "pady": 8}
        tk.Label(self, text="Website:").grid(row=0, column=0, sticky="w", **padding)
        self.website_entry = tk.Entry(self, width=40)
        self.website_entry.insert(0, self.credential["website"])
        self.website_entry.grid(row=0, column=1, **padding)

        tk.Label(self, text="Username:").grid(row=1, column=0, sticky="w", **padding)
        self.username_entry = tk.Entry(self, width=40)
        self.username_entry.insert(0, self.credential["username"])
        self.username_entry.grid(row=1, column=1, **padding)

        tk.Label(self, text="Password:").grid(row=2, column=0, sticky="w", **padding)
        self.password_entry = tk.Entry(self, width=40)
        self.password_entry.insert(0, self.credential["password"])
        self.password_entry.grid(row=2, column=1, **padding)

        generate_button = tk.Button(self, text="Generate", command=self._generate_password)
        generate_button.grid(row=2, column=2, sticky="w", **padding)

        tk.Label(self, text="Notes:").grid(row=3, column=0, sticky="nw", **padding)
        self.notes_text = tk.Text(self, width=40, height=6)
        self.notes_text.insert("1.0", self.credential["notes"])
        self.notes_text.grid(row=3, column=1, columnspan=2, **padding)

        button_frame = tk.Frame(self)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        save_button = tk.Button(button_frame, text="Save", command=self._save)
        save_button.pack(side="left", padx=10)
        cancel_button = tk.Button(button_frame, text="Cancel", command=self.destroy)
        cancel_button.pack(side="left", padx=10)

    def _generate_password(self) -> None:
        password = generate_password(
            length=18,
            use_upper=True,
            use_lower=True,
            use_digits=True,
            use_symbols=True,
        )
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, password)

    def _save(self) -> None:
        website = self.website_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        notes = self.notes_text.get("1.0", tk.END).rstrip("\n")

        if not website:
            messagebox.showwarning("Validation", "Website field cannot be empty.")
            return
        if not username:
            messagebox.showwarning("Validation", "Username field cannot be empty.")
            return
        if not password:
            messagebox.showwarning("Validation", "Password field cannot be empty.")
            return

        self.result = {
            "website": website,
            "username": username,
            "password": password,
            "notes": notes,
        }
        self.destroy()


class PasswordManagerApp:
    """Desktop application for creating and using the encrypted vault."""

    AUTO_LOCK_SECONDS = 300
    CLIPBOARD_CLEAR_SECONDS = 30

    def __init__(self):
        self.master_key = None
        self.vault_name = None
        self.is_switching = False
        self.root = tk.Tk()
        # Initially hide the main window while we ask which vault to open/create.
        self.root.withdraw()

        # Base folder where per-vault directories are stored.
        self.vaults_base = Path(__file__).resolve().parent.parent / "vaults"
        self.vaults_base.mkdir(parents=True, exist_ok=True)
        print(f"[DEBUG] Vaults base directory: {self.vaults_base}")

        selected_db_path, vault_name = self._select_or_create_vault()
        print(f"[DEBUG] Vault selected: {vault_name}, DB path: {selected_db_path}")
        self.vault_name = vault_name
        self.db = DatabaseManager(path=str(selected_db_path))
        self.root.title("Secure Local Password Manager")
        self.root.geometry("760x520")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.clipboard_manager = ClipboardManager(self.root, clear_seconds=self.CLIPBOARD_CLEAR_SECONDS)
        self.inactivity_handle = None

        self.search_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.password_confirm_var = tk.StringVar()
        self._bind_activity_events()
        self._show_login_screen()

    def _select_or_create_vault(self) -> tuple[Path, str]:
        """Prompt the user to pick an existing vault folder or create a new one.

        The vaults live under a `vaults/` directory next to the application.
        Returns tuple of (vault.db path, vault_name).
        If the user cancels, exit the application.
        """
        # Show the root window so dialogs can appear properly
        self.root.deiconify()
        self.root.geometry("1x1+0+0")  # Position it off-screen
        self.root.update()
        
        while True:
            existing = [p.name for p in self.vaults_base.iterdir() if p.is_dir() and (p / "vault.db").exists()]
            print(f"[DEBUG] Existing vaults: {existing}")
            
            dialog = VaultSelector(self.root, self.vaults_base, existing)
            self.root.wait_window(dialog)
            print(f"[DEBUG] Dialog closed, result: {dialog.result}")
            
            if dialog.result is None:
                # User cancelled; exit cleanly.
                self.root.destroy()
                raise SystemExit

            name = dialog.result.strip()
            if not name:
                messagebox.showwarning("Input Required", "Please enter a vault name.")
                continue

            selected_dir = self.vaults_base / name
            selected_dir.mkdir(parents=True, exist_ok=True)
            db_path = selected_dir / "vault.db"
            print(f"[DEBUG] Selected vault: {name}, DB path: {db_path}")
            # Hide root again
            self.root.withdraw()
            return db_path, name

    def _back_to_vault_selection(self) -> None:
        """Return to vault folder selection to switch to a different vault.

        Closes the current database connection, clears the master key,
        and re-opens the vault selection dialog.
        """
        self.db.close()
        self.master_key = None
        self.is_switching = True
        selected_db_path, vault_name = self._select_or_create_vault()
        self.vault_name = vault_name
        self.db = DatabaseManager(path=str(selected_db_path))
        self._show_login_screen()

    def run(self):
        self.root.mainloop()

    def _bind_activity_events(self) -> None:
        self.root.bind_all("<Key>", lambda event: self._reset_auto_lock())
        self.root.bind_all("<Button>", lambda event: self._reset_auto_lock())

    def _reset_auto_lock(self) -> None:
        if self.inactivity_handle is not None:
            self.root.after_cancel(self.inactivity_handle)
        self.inactivity_handle = self.root.after(self.AUTO_LOCK_SECONDS * 1000, self._lock_vault)

    def _lock_vault(self) -> None:
        self.master_key = None
        messagebox.showinfo("Auto Lock", "The vault has been locked due to inactivity.")
        self._show_login_screen()

    def _on_close(self) -> None:
        self.db.close()
        self.root.destroy()

    def _clear_screen(self) -> None:
        for widget in self.root.winfo_children():
            widget.destroy()

    def _show_login_screen(self) -> None:
        self._clear_screen()
        self.search_var.set("")
        self.password_var.set("")
        self.password_confirm_var.set("")

        # Show the root window for the login screen
        self.root.deiconify()

        # Main container with improved styling
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        frame = ttk.Frame(main_frame)
        frame.pack(expand=True)

        heading = ttk.Label(frame, text="Secure Password Vault", font=("Segoe UI", 20, "bold"))
        heading.grid(row=0, column=0, columnspan=2, pady=(0, 30))

        if self.is_switching:
            mode_text = f"Switching to vault: {self.vault_name}\nEnter the password to unlock"
            self.is_switching = False
        else:
            mode_text = "Create a master password" if not self.db.is_initialized() else f"Enter password for vault: {self.vault_name}"
        ttk.Label(frame, text=mode_text, font=("Segoe UI", 10), justify="center").grid(row=1, column=0, columnspan=2, pady=(0, 20))

        ttk.Label(frame, text="Master Password:", font=("Segoe UI", 10)).grid(row=2, column=0, sticky="e", padx=5, pady=8)
        self.password_entry = ttk.Entry(frame, width=30, textvariable=self.password_var, show="*")
        self.password_entry.grid(row=2, column=1, sticky="w", padx=5, pady=8)
        self.password_entry.focus()

        if not self.db.is_initialized():
            ttk.Label(frame, text="Confirm Password:", font=("Segoe UI", 10)).grid(row=3, column=0, sticky="e", padx=5, pady=8)
            self.confirm_entry = ttk.Entry(frame, width=30, textvariable=self.password_confirm_var, show="*")
            self.confirm_entry.grid(row=3, column=1, sticky="w", padx=5, pady=8)
            button_row = 4
        else:
            button_row = 3

        button_text = "Create Vault" if not self.db.is_initialized() else "Unlock Vault"
        action_button = ttk.Button(frame, text=button_text, command=self._handle_login)
        action_button.grid(row=button_row, column=0, columnspan=2, pady=25)

        info_label = ttk.Label(
            frame,
            text="The vault is encrypted locally. Keep your master password safe.",
            wraplength=380,
            justify="center",
            font=("Segoe UI", 9),
        )
        info_label.grid(row=button_row + 1, column=0, columnspan=2, pady=15)

    def _handle_login(self) -> None:
        password = self.password_var.get()
        if password == "":
            messagebox.showwarning("Validation", "Please enter a master password.")
            return

        if not self.db.is_initialized():
            confirmation = self.password_confirm_var.get()
            if confirmation == "":
                messagebox.showwarning("Validation", "Please confirm your master password.")
                return
            if password != confirmation:
                messagebox.showerror("Validation Error", "Master passwords do not match.")
                return
            if len(password) < 10:
                messagebox.showwarning("Validation", "Master password should be at least 10 characters.")
                return

            self.master_key = self.db.setup_master_password(password)
            messagebox.showinfo("Setup Complete", "Master password created successfully.")
            self._show_vault_screen()
            return

        key = self.db.authenticate_master_password(password)
        if key is None:
            messagebox.showerror("Authentication Failed", "Master password is incorrect.")
            return

        self.master_key = key
        self._show_vault_screen()

    def _ensure_unlocked(self) -> bool:
        if self.master_key is None:
            messagebox.showerror(
                "Vault Locked",
                "The vault is locked or your session has expired. Please unlock with your master password.",
            )
            self._show_login_screen()
            return False
        return True

    def _show_vault_screen(self) -> None:
        if not self._ensure_unlocked():
            return
        self._clear_screen()
        self._reset_auto_lock()

        header_frame = ttk.Frame(self.root, padding=12)
        header_frame.pack(fill="x")

        title = ttk.Label(header_frame, text=f"Vault: {self.vault_name}", font=("Segoe UI", 16, "bold"))
        title.pack(side="left")

        # Right-side buttons for vault navigation and adding credentials
        new_button = ttk.Button(header_frame, text="Add Credential", command=self._add_credential)
        new_button.pack(side="right", padx=5)

        back_button = ttk.Button(header_frame, text="Back", command=self._back_to_vault_selection)
        back_button.pack(side="right", padx=5)

        search_frame = ttk.Frame(self.root, padding=(12, 0, 12, 6))
        search_frame.pack(fill="x")
        ttk.Label(search_frame, text="Search:").pack(side="left")
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=36)
        search_entry.pack(side="left", padx=6)
        self.search_var.trace_add("write", lambda *_: self._refresh_credentials())

        self.tree = ttk.Treeview(self.root, columns=("website", "username", "updated"), show="headings", height=14)
        self.tree.heading("website", text="Website")
        self.tree.heading("username", text="Username")
        self.tree.heading("updated", text="Last Updated")
        self.tree.column("website", width=260)
        self.tree.column("username", width=220)
        self.tree.column("updated", width=140)
        self.tree.pack(fill="both", expand=True, padx=12, pady=6)
        self.tree.bind("<Double-1>", lambda event: self._edit_selected())

        button_frame = ttk.Frame(self.root, padding=12)
        button_frame.pack(fill="x")
        edit_button = ttk.Button(button_frame, text="Edit", command=self._edit_selected)
        edit_button.pack(side="left", padx=4)
        delete_button = ttk.Button(button_frame, text="Delete", command=self._delete_selected)
        delete_button.pack(side="left", padx=4)
        copy_button = ttk.Button(button_frame, text="Copy Password", command=self._copy_selected_password)
        copy_button.pack(side="left", padx=4)

        self._refresh_credentials()

    def _refresh_credentials(self) -> None:
        if not self._ensure_unlocked():
            return

        search_value = self.search_var.get().strip().lower()
        for row in self.tree.get_children():
            self.tree.delete(row)

        credentials = self.db.list_credentials(self.master_key)
        for record in credentials:
            combined = f"{record['website']} {record['username']} {record.get('notes', '')}".lower()
            if search_value and search_value not in combined:
                continue
            self.tree.insert(
                "",
                tk.END,
                iid=str(record["id"]),
                values=(record["website"], record["username"], record["updated_at"]),
            )

    def _get_selected_id(self) -> int | None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Selection Required", "Please select a credential first.")
            return None
        return int(selection[0])

    def _add_credential(self) -> None:
        if not self._ensure_unlocked():
            return
        dialog = CredentialEditor(self.root, "Add Credential")
        if dialog.result:
            self.db.add_credential(dialog.result, self.master_key)
            self._refresh_credentials()

    def _edit_selected(self) -> None:
        if not self._ensure_unlocked():
            return
        record_id = self._get_selected_id()
        if record_id is None:
            return
        credential = self.db.get_credential(record_id, self.master_key)
        if credential is None:
            messagebox.showerror("Error", "Could not load the selected credential.")
            return
        dialog = CredentialEditor(self.root, "Edit Credential", credential)
        if dialog.result:
            self.db.update_credential(record_id, dialog.result, self.master_key)
            self._refresh_credentials()

    def _delete_selected(self) -> None:
        record_id = self._get_selected_id()
        if record_id is None:
            return
        if messagebox.askyesno("Confirm Delete", "Delete this credential permanently?"):
            self.db.delete_credential(record_id)
            self._refresh_credentials()

    def _copy_selected_password(self) -> None:
        if not self._ensure_unlocked():
            return
        record_id = self._get_selected_id()
        if record_id is None:
            return
        credential = self.db.get_credential(record_id, self.master_key)
        if credential is None:
            messagebox.showerror("Error", "Could not load the selected credential.")
            return
        self.clipboard_manager.copy_to_clipboard(credential["password"])
        messagebox.showinfo(
            "Copied",
            f"Password copied to clipboard. It will be cleared in {self.CLIPBOARD_CLEAR_SECONDS} seconds.",
        )
