import tkinter as tk


class ClipboardManager:
    """Manage the Tkinter clipboard and clear it automatically."""

    def __init__(self, root: tk.Tk, clear_seconds: int = 30) -> None:
        self.root = root
        self.clear_seconds = clear_seconds
        self.clear_handle = None

    def copy_to_clipboard(self, text: str) -> None:
        """Copy text to the clipboard and schedule automatic clearing."""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        if self.clear_handle is not None:
            self.root.after_cancel(self.clear_handle)
        self.clear_handle = self.root.after(self.clear_seconds * 1000, self.clear_clipboard)

    def clear_clipboard(self) -> None:
        """Clear the clipboard contents safely."""
        try:
            self.root.clipboard_clear()
        except tk.TclError:
            pass
        self.clear_handle = None
