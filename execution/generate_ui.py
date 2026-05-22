#!/usr/bin/env python3
"""
generate_ui.py — Simple GUI for Google Flow image/video generation.

Usage:
    .venv/bin/python execution/generate_ui.py
"""

import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "google-flow-generator" / "scripts" / "generate.py"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"


class GenerateApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Google Flow Generator")
        self.resizable(False, False)
        self._build_ui()
        self._process = None

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}
        frame = ttk.Frame(self, padding=16)
        frame.grid(sticky="nsew")

        row = 0

        # ── Type ──────────────────────────────────────────────────────────────
        ttk.Label(frame, text="Type").grid(row=row, column=0, sticky="w", **pad)
        self.type_var = tk.StringVar(value="image")
        type_frame = ttk.Frame(frame)
        type_frame.grid(row=row, column=1, sticky="w", **pad)
        ttk.Radiobutton(type_frame, text="Image", variable=self.type_var, value="image").pack(side="left", padx=(0, 12))
        ttk.Radiobutton(type_frame, text="Video", variable=self.type_var, value="video").pack(side="left")
        row += 1

        # ── Spreadsheet ───────────────────────────────────────────────────────
        ttk.Label(frame, text="Spreadsheet").grid(row=row, column=0, sticky="w", **pad)
        xlsx_frame = ttk.Frame(frame)
        xlsx_frame.grid(row=row, column=1, sticky="ew", **pad)
        self.xlsx_var = tk.StringVar()
        ttk.Entry(xlsx_frame, textvariable=self.xlsx_var, width=48).pack(side="left", padx=(0, 6))
        ttk.Button(xlsx_frame, text="Browse…", command=self._browse_xlsx).pack(side="left")
        row += 1

        # ── Row number ────────────────────────────────────────────────────────
        ttk.Label(frame, text="Row #").grid(row=row, column=0, sticky="w", **pad)
        self.row_var = tk.IntVar(value=1)
        ttk.Spinbox(frame, textvariable=self.row_var, from_=1, to=9999, width=8).grid(
            row=row, column=1, sticky="w", **pad)
        row += 1

        # ── Output folder ─────────────────────────────────────────────────────
        ttk.Label(frame, text="Output Folder").grid(row=row, column=0, sticky="w", **pad)
        out_frame = ttk.Frame(frame)
        out_frame.grid(row=row, column=1, sticky="ew", **pad)
        self.out_var = tk.StringVar(value=str(ROOT / "output"))
        ttk.Entry(out_frame, textvariable=self.out_var, width=48).pack(side="left", padx=(0, 6))
        ttk.Button(out_frame, text="Browse…", command=self._browse_out).pack(side="left")
        row += 1

        # ── Generate button ───────────────────────────────────────────────────
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(8, 4))
        self.generate_btn = ttk.Button(btn_frame, text="Generate", command=self._run, width=20)
        self.generate_btn.pack(side="left", padx=6)
        self.cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self._cancel, width=12, state="disabled")
        self.cancel_btn.pack(side="left", padx=6)
        row += 1

        # ── Log output ────────────────────────────────────────────────────────
        ttk.Label(frame, text="Log").grid(row=row, column=0, sticky="nw", **pad)
        self.log = scrolledtext.ScrolledText(frame, width=72, height=18, state="disabled",
                                             font=("Menlo", 11), bg="#1e1e1e", fg="#d4d4d4",
                                             insertbackground="white")
        self.log.grid(row=row, column=1, sticky="ew", **pad)
        row += 1

        # ── Status bar ────────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(frame, textvariable=self.status_var, foreground="gray").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 4))

    # ── File pickers ──────────────────────────────────────────────────────────

    def _browse_xlsx(self):
        path = filedialog.askopenfilename(
            title="Select spreadsheet",
            filetypes=[("Excel files", "*.xlsx *.xlsm"), ("All files", "*.*")],
        )
        if path:
            self.xlsx_var.set(path)

    def _browse_out(self):
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self.out_var.set(path)

    # ── Generation ────────────────────────────────────────────────────────────

    def _run(self):
        xlsx = self.xlsx_var.get().strip()
        out  = self.out_var.get().strip()

        if not xlsx:
            self._log("ERROR: Please select a spreadsheet.\n", error=True)
            return
        if not Path(xlsx).exists():
            self._log(f"ERROR: File not found: {xlsx}\n", error=True)
            return
        if not out:
            self._log("ERROR: Please select an output folder.\n", error=True)
            return

        Path(out).mkdir(parents=True, exist_ok=True)

        cmd = [
            str(VENV_PYTHON),
            str(SCRIPT),
            "--xlsx", xlsx,
            "--row",  str(self.row_var.get()),
            "--type", self.type_var.get(),
            "--out",  out,
        ]

        self._log(f"Running: {' '.join(cmd)}\n\n")
        self.generate_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.status_var.set("Generating…")

        threading.Thread(target=self._run_subprocess, args=(cmd,), daemon=True).start()

    def _run_subprocess(self, cmd):
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            for line in self._process.stdout:
                self.after(0, self._log, line)
            self._process.wait()
            rc = self._process.returncode
            if rc == 0:
                self.after(0, self.status_var.set, "Done ✅")
            elif rc == -15:
                self.after(0, self.status_var.set, "Cancelled")
            else:
                self.after(0, self.status_var.set, f"Failed (exit {rc})")
        except Exception as e:
            self.after(0, self._log, f"ERROR: {e}\n", True)
            self.after(0, self.status_var.set, "Error")
        finally:
            self._process = None
            self.after(0, self.generate_btn.config, {"state": "normal"})
            self.after(0, self.cancel_btn.config,   {"state": "disabled"})

    def _cancel(self):
        if self._process:
            self._process.terminate()
            self._log("\n[Cancelled]\n")
            self.status_var.set("Cancelling…")

    # ── Logging ───────────────────────────────────────────────────────────────

    def _log(self, text: str, error: bool = False):
        self.log.config(state="normal")
        tag = "error" if error else None
        self.log.insert("end", text, tag)
        self.log.tag_config("error", foreground="#f48771")
        self.log.see("end")
        self.log.config(state="disabled")


if __name__ == "__main__":
    app = GenerateApp()
    app.mainloop()
