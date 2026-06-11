"""
gui/main_window.py
==================
EmotionSense AI — Complete GUI built with customtkinter.

Screens
-------
  LoginScreen  — signup / login
  MainApp      — sidebar + content frames:
        Dashboard · Analyze · Voice · History · Analytics · Reports · Settings
"""

from __future__ import annotations

import json
import os
import threading
import tkinter as tk
import tkinter.messagebox as mb
import tkinter.ttk as ttk
from typing import Optional

try:
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
except ImportError:
    raise SystemExit(
        "customtkinter not installed.\n"
        "Run: pip install customtkinter"
    )

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from database.db_manager import DatabaseManager
from models.emotion_analyzer import EmotionAnalyzer
from voice.voice_handler import VoiceHandler
from analytics import charts
from reports import report_generator
from utils.helpers import (get_emoji, get_color, format_datetime,
                           open_file, stress_label)

# ── Palette ───────────────────────────────────────────────────────────────────
C = {
    "bg":        "#0f0e17",
    "panel":     "#1a1a2e",
    "sidebar":   "#16213e",
    "card":      "#1f2b47",
    "accent":    "#7c6aff",
    "accent2":   "#ff6b6b",
    "text":      "#e0e0e0",
    "muted":     "#8888aa",
    "success":   "#2ECC71",
    "warning":   "#F1C40F",
    "danger":    "#E74C3C",
    "border":    "#2a2a4a",
}
FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_HEADING= ("Segoe UI", 14, "bold")
FONT_BODY   = ("Segoe UI", 11)
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 10)


# ════════════════════════════════════════════════════════════════════════════
# Login / Signup Screen
# ════════════════════════════════════════════════════════════════════════════

class LoginScreen(ctk.CTkToplevel):
    """Modal login / signup window."""

    def __init__(self, db: DatabaseManager, on_login):
        super().__init__()
        self.db = db
        self.on_login = on_login
        self.title("EmotionSense AI — Login")
        self.geometry("420x520")
        self.resizable(False, False)
        self.configure(fg_color=C["panel"])
        self._mode = "login"       # 'login' | 'signup'
        self._build()
        self.grab_set()            # modal

    def _build(self):
        # Logo / brand
        ctk.CTkLabel(self, text="🧠 EmotionSense AI",
                      font=FONT_TITLE, text_color=C["accent"]).pack(pady=(30, 4))
        ctk.CTkLabel(self, text="Mental Wellness Monitoring System",
                      font=FONT_SMALL, text_color=C["muted"]).pack()

        self._tab_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._tab_frame.pack(pady=20)
        self._btn_login = ctk.CTkButton(
            self._tab_frame, text="Login", width=90, corner_radius=20,
            fg_color=C["accent"], command=lambda: self._switch("login"))
        self._btn_login.grid(row=0, column=0, padx=4)
        self._btn_signup = ctk.CTkButton(
            self._tab_frame, text="Sign Up", width=90, corner_radius=20,
            fg_color=C["card"], command=lambda: self._switch("signup"))
        self._btn_signup.grid(row=0, column=1, padx=4)

        self._form = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16)
        self._form.pack(padx=30, fill="x")
        self._build_form()

        self._err_lbl = ctk.CTkLabel(self, text="", text_color=C["danger"],
                                      font=FONT_SMALL, wraplength=360)
        self._err_lbl.pack(pady=6)

        self._submit_btn = ctk.CTkButton(
            self, text="Login", height=42, corner_radius=12,
            font=("Segoe UI", 12, "bold"), fg_color=C["accent"],
            command=self._submit)
        self._submit_btn.pack(padx=30, pady=4, fill="x")

        ctk.CTkLabel(self, text="Your data is stored locally and privately. 🔒",
                      font=FONT_SMALL, text_color=C["muted"]).pack(pady=10)

    def _build_form(self):
        for w in self._form.winfo_children():
            w.destroy()
        pad = {"padx": 20, "pady": 6, "fill": "x"}

        ctk.CTkLabel(self._form, text="Username", font=FONT_SMALL,
                      text_color=C["muted"]).pack(**pad)
        self._user_entry = ctk.CTkEntry(self._form, height=38,
                                         placeholder_text="Enter username")
        self._user_entry.pack(**pad)

        if self._mode == "signup":
            ctk.CTkLabel(self._form, text="Email (optional)", font=FONT_SMALL,
                          text_color=C["muted"]).pack(**pad)
            self._email_entry = ctk.CTkEntry(self._form, height=38,
                                              placeholder_text="you@example.com")
            self._email_entry.pack(**pad)

        ctk.CTkLabel(self._form, text="Password", font=FONT_SMALL,
                      text_color=C["muted"]).pack(**pad)
        self._pass_entry = ctk.CTkEntry(self._form, height=38, show="•",
                                         placeholder_text="Enter password")
        self._pass_entry.pack(**pad)
        self._pass_entry.bind("<Return>", lambda _: self._submit())

        if self._mode == "signup":
            ctk.CTkLabel(self._form, text="Confirm Password", font=FONT_SMALL,
                          text_color=C["muted"]).pack(**pad)
            self._pass2_entry = ctk.CTkEntry(self._form, height=38, show="•",
                                              placeholder_text="Repeat password")
            self._pass2_entry.pack(**pad)

    def _switch(self, mode: str):
        self._mode = mode
        self._btn_login.configure(
            fg_color=C["accent"] if mode == "login" else C["card"])
        self._btn_signup.configure(
            fg_color=C["accent"] if mode == "signup" else C["card"])
        self._submit_btn.configure(text="Login" if mode == "login" else "Create Account")
        self._err_lbl.configure(text="")
        self._build_form()

    def _submit(self):
        username = self._user_entry.get().strip()
        password = self._pass_entry.get().strip()

        if self._mode == "signup":
            p2 = self._pass2_entry.get().strip()
            if password != p2:
                self._err_lbl.configure(text="Passwords do not match.")
                return
            ok, msg = self.db.register_user(username, password)
            if not ok:
                self._err_lbl.configure(text=msg)
                return
            self._err_lbl.configure(text=msg, text_color=C["success"])
            self._switch("login")
        else:
            ok, user = self.db.authenticate_user(username, password)
            if not ok:
                self._err_lbl.configure(text="Incorrect username or password.")
                return
            self.destroy()
            self.on_login(user)


# ════════════════════════════════════════════════════════════════════════════
# Main Application Window
# ════════════════════════════════════════════════════════════════════════════

class EmotionSenseApp(ctk.CTk):
    """Root window — shown after successful login."""

    def __init__(self):
        super().__init__()
        self.title("EmotionSense AI")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=C["bg"])

        self.db       = DatabaseManager()
        self.db.initialize()
        self.analyzer = EmotionAnalyzer()
        self.voice    = VoiceHandler()

        self.current_user: Optional[dict] = None
        self._last_result: Optional[dict] = None
        self._frames: dict[str, ctk.CTkFrame] = {}

        # Show login before drawing main UI
        self._show_login()

    # ── Login flow ────────────────────────────────────────────────────────
    def _show_login(self):
        self.withdraw()
        LoginScreen(self.db, self._on_login)

    def _on_login(self, user: dict):
        self.current_user = user
        self.deiconify()
        self._build_main_ui()

    # ── Main UI construction ──────────────────────────────────────────────
    def _build_main_ui(self):
        # Destroy anything left from a previous session
        for w in self.winfo_children():
            w.destroy()

        # ── Root layout: sidebar | content ───────────────────────────────
        self._sidebar = ctk.CTkFrame(self, width=210, fg_color=C["sidebar"],
                                      corner_radius=0)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        self._content = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self._build_pages()
        self._navigate("Dashboard")

    # ── Sidebar ───────────────────────────────────────────────────────────
    _NAV_ITEMS = [
        ("🏠", "Dashboard"),
        ("🔍", "Analyze"),
        ("🎙️", "Voice"),
        ("📋", "History"),
        ("📊", "Analytics"),
        ("📄", "Reports"),
        ("⚙️", "Settings"),
    ]

    def _build_sidebar(self):
        # Brand
        ctk.CTkLabel(self._sidebar, text="🧠", font=("Segoe UI", 32)
                      ).pack(pady=(24, 4))
        ctk.CTkLabel(self._sidebar, text="EmotionSense",
                      font=("Segoe UI", 14, "bold"),
                      text_color=C["accent"]).pack()
        ctk.CTkLabel(self._sidebar, text="AI  •  Wellness Monitor",
                      font=FONT_SMALL, text_color=C["muted"]).pack(pady=(0, 20))

        self._nav_btns: dict[str, ctk.CTkButton] = {}
        for icon, label in self._NAV_ITEMS:
            btn = ctk.CTkButton(
                self._sidebar,
                text=f"  {icon}  {label}",
                anchor="w",
                height=42,
                corner_radius=10,
                fg_color="transparent",
                hover_color=C["card"],
                font=FONT_BODY,
                command=lambda l=label: self._navigate(l),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_btns[label] = btn

        # Spacer + user info + logout
        ctk.CTkFrame(self._sidebar, height=2, fg_color=C["border"]
                      ).pack(fill="x", padx=10, pady=12)
        uname = self.current_user["username"]
        ctk.CTkLabel(self._sidebar, text=f"👤 {uname}",
                      font=FONT_SMALL, text_color=C["muted"]).pack(pady=4)
        ctk.CTkButton(
            self._sidebar, text="Logout", height=34, corner_radius=8,
            fg_color=C["danger"], hover_color="#a93226",
            font=FONT_SMALL, command=self._logout
        ).pack(fill="x", padx=10, pady=(4, 16))

    # ── Page container ────────────────────────────────────────────────────
    def _build_pages(self):
        builders = {
            "Dashboard": self._build_dashboard,
            "Analyze":   self._build_analyze,
            "Voice":     self._build_voice,
            "History":   self._build_history,
            "Analytics": self._build_analytics,
            "Reports":   self._build_reports,
            "Settings":  self._build_settings,
        }
        for name, builder in builders.items():
            frame = ctk.CTkFrame(self._content, fg_color=C["bg"],
                                  corner_radius=0)
            frame.place(relwidth=1, relheight=1)
            builder(frame)
            self._frames[name] = frame

    def _navigate(self, name: str):
        for lbl, btn in self._nav_btns.items():
            btn.configure(fg_color=C["accent"] if lbl == name else "transparent")
        self._frames[name].lift()
        if name == "History":
            self._refresh_history()
        if name == "Analytics":
            self._refresh_analytics()
        if name == "Dashboard":
            self._refresh_dashboard()

    # ════════════════════════════════════════════════════════════════════
    # PAGE: Dashboard
    # ════════════════════════════════════════════════════════════════════
    def _build_dashboard(self, f: ctk.CTkFrame):
        self._dash_frame = f

        header = ctk.CTkFrame(f, fg_color=C["panel"], corner_radius=0, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Welcome back 👋",
                      font=FONT_TITLE, text_color=C["text"]).pack(side="left", padx=24, pady=16)

        # Stat cards row
        self._dash_cards = ctk.CTkFrame(f, fg_color="transparent")
        self._dash_cards.pack(fill="x", padx=20, pady=16)

        # Last result area
        self._dash_result = ctk.CTkFrame(f, fg_color=C["card"], corner_radius=16)
        self._dash_result.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        ctk.CTkLabel(self._dash_result,
                      text="Run an analysis to see your latest emotion here 💡",
                      font=FONT_BODY, text_color=C["muted"]).pack(expand=True)

    def _refresh_dashboard(self):
        if self.current_user is None:
            return
        stats = self.db.get_stats(self.current_user["id"])

        # Rebuild stat cards
        for w in self._dash_cards.winfo_children():
            w.destroy()

        top_em = (stats["frequency"][0]["primary_emotion"]
                  if stats["frequency"] else "—")

        cards_data = [
            ("📊 Sessions", str(stats["total"]), C["accent"]),
            ("😊 Top Emotion", f"{get_emoji(top_em)} {top_em}", C["success"]),
            ("🔥 Avg Stress", f"{stats['avg_stress']}%", C["warning"]),
        ]

        for i, (title, value, color) in enumerate(cards_data):
            card = ctk.CTkFrame(self._dash_cards, fg_color=C["card"],
                                 corner_radius=14)
            card.grid(row=0, column=i, padx=8, sticky="ew")
            self._dash_cards.columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=title, font=FONT_SMALL,
                          text_color=C["muted"]).pack(pady=(12, 2))
            ctk.CTkLabel(card, text=value, font=("Segoe UI", 20, "bold"),
                          text_color=color).pack(pady=(0, 12))

        # Latest result
        for w in self._dash_result.winfo_children():
            w.destroy()

        if self._last_result:
            r = self._last_result
            em_color, _ = get_color(r["primary_emotion"])
            ctk.CTkLabel(self._dash_result,
                          text=f"{get_emoji(r['primary_emotion'])} {r['primary_emotion']}",
                          font=("Segoe UI", 36, "bold"),
                          text_color=em_color).pack(pady=(24, 4))
            ctk.CTkLabel(self._dash_result,
                          text=f"Confidence: {r['confidence']:.1f}%  •  "
                               f"Stress: {r['stress_level']:.1f}%",
                          font=FONT_BODY, text_color=C["muted"]).pack()
            if r.get("tips"):
                ctk.CTkLabel(self._dash_result,
                              text=r["tips"][0],
                              font=FONT_BODY, text_color=C["text"],
                              wraplength=600).pack(pady=(16, 0))
        else:
            ctk.CTkLabel(self._dash_result,
                          text="Run an analysis to see your latest emotion here 💡",
                          font=FONT_BODY, text_color=C["muted"]).pack(expand=True)

    # ════════════════════════════════════════════════════════════════════
    # PAGE: Analyze
    # ════════════════════════════════════════════════════════════════════
    def _build_analyze(self, f: ctk.CTkFrame):
        # Header
        hdr = ctk.CTkFrame(f, fg_color=C["panel"], corner_radius=0, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🔍 Emotion Analysis",
                      font=FONT_TITLE, text_color=C["text"]).pack(side="left", padx=24, pady=16)

        # Input area
        input_card = ctk.CTkFrame(f, fg_color=C["card"], corner_radius=16)
        input_card.pack(fill="x", padx=20, pady=16)
        ctk.CTkLabel(input_card, text="How are you feeling today?",
                      font=FONT_HEADING, text_color=C["accent"]).pack(anchor="w", padx=16, pady=(14, 4))
        self._analyze_text = ctk.CTkTextbox(
            input_card, height=90, font=FONT_BODY,
            fg_color=C["panel"], text_color=C["text"],
            border_color=C["border"], border_width=1, corner_radius=10)
        self._analyze_text.pack(fill="x", padx=16, pady=(0, 10))
        self._analyze_text.insert("0.0",
            "Type your thoughts here, e.g.:\n"
            "'I feel very stressed today and can't stop worrying about deadlines.'")

        btn_row = ctk.CTkFrame(input_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkButton(
            btn_row, text="✨ Analyze Now", height=40, corner_radius=12,
            fg_color=C["accent"], font=("Segoe UI", 12, "bold"),
            command=self._run_analysis).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            btn_row, text="🗑️ Clear", height=40, corner_radius=12,
            fg_color=C["card"], border_color=C["border"], border_width=1,
            command=lambda: (
                self._analyze_text.delete("0.0", "end")
            )).pack(side="left")

        # Results area — 2 columns
        self._result_area = ctk.CTkFrame(f, fg_color="transparent")
        self._result_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self._result_area.columnconfigure(0, weight=1)
        self._result_area.columnconfigure(1, weight=1)

        # Left: main emotion card
        self._em_card = ctk.CTkFrame(self._result_area, fg_color=C["card"],
                                      corner_radius=16)
        self._em_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        ctk.CTkLabel(self._em_card,
                      text="Your emotion analysis will appear here.",
                      text_color=C["muted"], wraplength=300).pack(expand=True)

        # Right: bar chart
        self._chart_card = ctk.CTkFrame(self._result_area, fg_color=C["card"],
                                         corner_radius=16)
        self._chart_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        ctk.CTkLabel(self._chart_card, text="Confidence chart",
                      text_color=C["muted"]).pack(expand=True)

    def _run_analysis(self, text: str = None, source: str = "text"):
        if text is None:
            text = self._analyze_text.get("0.0", "end").strip()
        if not text:
            mb.showwarning("Empty Input", "Please enter some text first.")
            return

        result = self.analyzer.analyze(text)
        self._last_result = result

        # Save to DB
        self.db.log_emotion(
            user_id      = self.current_user["id"],
            input_text   = text[:500],
            source       = source,
            primary_emotion = result["primary_emotion"],
            confidence   = result["confidence"],
            stress_level = result["stress_level"],
            all_scores   = result["scores_json"],
        )

        # Emergency check
        if result["is_emergency"]:
            mb.showwarning("⚠️ Emergency Support", result["emergency_message"])

        # Update emotion card
        for w in self._em_card.winfo_children():
            w.destroy()
        em = result["primary_emotion"]
        em_color, _ = get_color(em)
        s_label, s_color = stress_label(result["stress_level"])

        ctk.CTkLabel(self._em_card, text=get_emoji(em),
                      font=("Segoe UI", 44)).pack(pady=(20, 4))
        ctk.CTkLabel(self._em_card, text=em,
                      font=("Segoe UI", 22, "bold"),
                      text_color=em_color).pack()
        ctk.CTkLabel(self._em_card,
                      text=f"Confidence: {result['confidence']:.1f}%",
                      font=FONT_BODY, text_color=C["muted"]).pack(pady=2)

        # Stress bar
        ctk.CTkLabel(self._em_card, text=f"Stress Level: {s_label}",
                      font=FONT_SMALL, text_color=s_color).pack(pady=2)
        ctk.CTkProgressBar(self._em_card, progress_color=s_color,
                            fg_color=C["panel"], height=8
                            ).pack(fill="x", padx=20, pady=(2, 12))

        ctk.CTkLabel(self._em_card, text="💡 Wellness Tips",
                      font=FONT_HEADING, text_color=C["text"]).pack(anchor="w", padx=16)
        for tip in result["tips"]:
            ctk.CTkLabel(self._em_card, text=f"  • {tip}",
                          font=FONT_SMALL, text_color=C["text"],
                          wraplength=300, justify="left").pack(anchor="w", padx=16, pady=2)

        # Chatbot-style suggestion
        self._add_chatbot_row(self._em_card, em)

        # Update bar chart
        for w in self._chart_card.winfo_children():
            w.destroy()
        fig = charts.emotion_bar_chart(result["scores"])
        canvas = FigureCanvasTkAgg(fig, self._chart_card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    def _add_chatbot_row(self, parent, emotion: str):
        SUGGESTIONS = {
            "Stressed": "Would you like a 5-minute breathing exercise? 🧘",
            "Anxious":  "Shall I guide you through a grounding exercise? 🌿",
            "Sad":      "Would you like to read some uplifting quotes? 📖",
            "Angry":    "Try box breathing: inhale 4s · hold 4s · exhale 4s.",
            "Fearful":  "Remember: this feeling is temporary. You've got this 💪",
            "Happy":    "Keep this energy going — share it with someone! 😊",
            "Excited":  "Channel this into something productive you've been putting off!",
            "Neutral":  "A great time for mindful journalling. 📓",
        }
        msg = SUGGESTIONS.get(emotion, "Take care of yourself today. 💙")
        bubble = ctk.CTkFrame(parent, fg_color="#1e3a5f", corner_radius=12)
        bubble.pack(fill="x", padx=16, pady=(12, 16))
        ctk.CTkLabel(bubble, text="🤖  AI Assistant",
                      font=FONT_SMALL, text_color=C["accent"]).pack(anchor="w", padx=10, pady=(8, 0))
        ctk.CTkLabel(bubble, text=msg, font=FONT_SMALL,
                      text_color=C["text"], wraplength=280,
                      justify="left").pack(anchor="w", padx=10, pady=(2, 10))

    # ════════════════════════════════════════════════════════════════════
    # PAGE: Voice
    # ════════════════════════════════════════════════════════════════════
    def _build_voice(self, f: ctk.CTkFrame):
        hdr = ctk.CTkFrame(f, fg_color=C["panel"], corner_radius=0, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🎙️ Voice Analysis",
                      font=FONT_TITLE, text_color=C["text"]).pack(side="left", padx=24, pady=16)

        center = ctk.CTkFrame(f, fg_color="transparent")
        center.pack(expand=True)

        ctk.CTkLabel(center, text="🎙️",
                      font=("Segoe UI", 64)).pack(pady=(0, 12))
        ctk.CTkLabel(center,
                      text="Click the button and speak your feelings.\n"
                           "Your voice will be transcribed and analyzed.",
                      font=FONT_BODY, text_color=C["muted"],
                      justify="center").pack(pady=(0, 20))

        self._voice_status = ctk.CTkLabel(center, text="Ready to listen",
                                           font=FONT_BODY, text_color=C["muted"])
        self._voice_status.pack(pady=8)

        self._voice_btn = ctk.CTkButton(
            center, text="🎤  Start Listening", height=52, width=220,
            corner_radius=14, font=("Segoe UI", 14, "bold"),
            fg_color=C["accent"], command=self._start_voice)
        self._voice_btn.pack(pady=8)

        self._voice_text_box = ctk.CTkTextbox(
            center, height=80, width=520, font=FONT_MONO,
            fg_color=C["card"], text_color=C["text"], state="disabled",
            corner_radius=10)
        self._voice_text_box.pack(pady=12)

        if not self.voice.available:
            ctk.CTkLabel(center,
                          text="⚠️  Voice unavailable — install speechrecognition + pyaudio",
                          font=FONT_SMALL, text_color=C["warning"]).pack()

    def _start_voice(self):
        if not self.voice.available:
            mb.showwarning("Unavailable",
                            "Install speechrecognition and pyaudio to use voice input.")
            return
        self._voice_btn.configure(state="disabled", text="🔴  Listening…")
        self._voice_status.configure(text="Listening… speak now", text_color=C["warning"])

        def _on_result(text, error):
            self.after(0, lambda: self._handle_voice_result(text, error))

        self.voice.listen(on_result=_on_result, timeout=8)

    def _handle_voice_result(self, text: Optional[str], error: Optional[str]):
        self._voice_btn.configure(state="normal", text="🎤  Start Listening")
        if error:
            self._voice_status.configure(text=f"⚠️ {error}", text_color=C["danger"])
            return

        self._voice_status.configure(text=f"✅ Detected speech. Analyzing…",
                                      text_color=C["success"])
        self._voice_text_box.configure(state="normal")
        self._voice_text_box.delete("0.0", "end")
        self._voice_text_box.insert("0.0", text)
        self._voice_text_box.configure(state="disabled")

        # Pre-fill analyze tab and navigate there
        self._analyze_text.delete("0.0", "end")
        self._analyze_text.insert("0.0", text)
        self._run_analysis(text=text, source="voice")
        self._navigate("Analyze")

    # ════════════════════════════════════════════════════════════════════
    # PAGE: History
    # ════════════════════════════════════════════════════════════════════
    def _build_history(self, f: ctk.CTkFrame):
        hdr = ctk.CTkFrame(f, fg_color=C["panel"], corner_radius=0, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="📋 Emotion History",
                      font=FONT_TITLE, text_color=C["text"]).pack(side="left", padx=24, pady=16)
        ctk.CTkButton(hdr, text="🗑️ Clear All", height=34, width=110,
                       corner_radius=8, fg_color=C["danger"],
                       command=self._clear_history).pack(side="right", padx=24, pady=18)

        # Treeview with scrollbar
        tree_frame = ctk.CTkFrame(f, fg_color=C["card"], corner_radius=16)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=16)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                         background=C["card"], fieldbackground=C["card"],
                         foreground=C["text"], rowheight=32,
                         font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                         background=C["sidebar"], foreground=C["accent"],
                         font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", C["accent"])])

        cols = ("#", "Time", "Emotion", "Confidence", "Stress", "Source", "Text")
        self._hist_tree = ttk.Treeview(tree_frame, columns=cols,
                                        show="headings", selectmode="browse")
        widths = [40, 140, 100, 90, 80, 70, 280]
        for col, w in zip(cols, widths):
            self._hist_tree.heading(col, text=col)
            self._hist_tree.column(col, width=w, minwidth=w)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                             command=self._hist_tree.yview)
        self._hist_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._hist_tree.pack(fill="both", expand=True, padx=10, pady=10)

    def _refresh_history(self):
        if not hasattr(self, "_hist_tree"):
            return
        for row in self._hist_tree.get_children():
            self._hist_tree.delete(row)
        history = self.db.get_history(self.current_user["id"])
        for i, rec in enumerate(history, 1):
            em  = rec["primary_emotion"]
            tag = em.lower()
            self._hist_tree.insert(
                "", "end", tags=(tag,),
                values=(i,
                        rec["timestamp"][:16],
                        f"{get_emoji(em)} {em}",
                        f"{rec['confidence']:.1f}%",
                        f"{rec['stress_level']:.1f}%",
                        rec["source"],
                        rec["input_text"][:60] + "…" if len(rec.get("input_text","")) > 60
                        else rec.get("input_text", ""))
            )

    def _clear_history(self):
        if mb.askyesno("Clear History",
                        "Delete ALL emotion history? This cannot be undone."):
            self.db.delete_history(self.current_user["id"])
            self._refresh_history()

    # ════════════════════════════════════════════════════════════════════
    # PAGE: Analytics
    # ════════════════════════════════════════════════════════════════════
    def _build_analytics(self, f: ctk.CTkFrame):
        hdr = ctk.CTkFrame(f, fg_color=C["panel"], corner_radius=0, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="📊 Analytics Dashboard",
                      font=FONT_TITLE, text_color=C["text"]).pack(side="left", padx=24, pady=16)
        ctk.CTkButton(hdr, text="🔄 Refresh", height=34, width=90,
                       corner_radius=8, fg_color=C["accent"],
                       command=self._refresh_analytics).pack(side="right", padx=24, pady=18)

        self._analytics_scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        self._analytics_scroll.pack(fill="both", expand=True, padx=20, pady=16)

    def _refresh_analytics(self):
        if not hasattr(self, "_analytics_scroll"):
            return
        for w in self._analytics_scroll.winfo_children():
            w.destroy()

        history = self.db.get_history(self.current_user["id"])
        stats   = self.db.get_stats(self.current_user["id"])

        # Row 1: pie + bar
        row1 = ctk.CTkFrame(self._analytics_scroll, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 16))
        row1.columnconfigure(0, weight=1)
        row1.columnconfigure(1, weight=1)

        self._embed_chart(row1, charts.emotion_pie_chart(stats["frequency"]),
                           "Emotion Frequency", 0, 0)
        self._embed_chart(row1, charts.weekly_bar_chart(stats["weekly"]),
                           "This Week", 0, 1)

        # Row 2: stress trend (full width)
        row2 = ctk.CTkFrame(self._analytics_scroll, fg_color="transparent")
        row2.pack(fill="x")
        self._embed_chart(row2, charts.stress_trend_chart(history),
                           "Stress Trend", 0, 0, colspan=1)

    def _embed_chart(self, parent, fig, title: str, row: int, col: int,
                     colspan: int = 1):
        card = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=14)
        card.grid(row=row, column=col, columnspan=colspan,
                  padx=8, pady=4, sticky="nsew")
        ctk.CTkLabel(card, text=title, font=FONT_HEADING,
                      text_color=C["text"]).pack(anchor="w", padx=14, pady=(10, 0))
        canvas = FigureCanvasTkAgg(fig, card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    # ════════════════════════════════════════════════════════════════════
    # PAGE: Reports
    # ════════════════════════════════════════════════════════════════════
    def _build_reports(self, f: ctk.CTkFrame):
        hdr = ctk.CTkFrame(f, fg_color=C["panel"], corner_radius=0, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="📄 Reports & Export",
                      font=FONT_TITLE, text_color=C["text"]).pack(side="left", padx=24, pady=16)

        center = ctk.CTkFrame(f, fg_color="transparent")
        center.pack(expand=True)

        ctk.CTkLabel(center, text="Export your emotion data in multiple formats.",
                      font=FONT_BODY, text_color=C["muted"]).pack(pady=(0, 30))

        buttons = [
            ("📄  Generate PDF Report", C["accent"],  self._export_pdf),
            ("📊  Export to CSV",        C["success"], self._export_csv),
            ("📈  Export to Excel",      "#16a085",    self._export_excel),
        ]
        for text, color, cmd in buttons:
            ctk.CTkButton(center, text=text, height=48, width=280,
                           corner_radius=12, font=("Segoe UI", 13, "bold"),
                           fg_color=color, command=cmd).pack(pady=8)

        self._report_status = ctk.CTkLabel(center, text="",
                                            font=FONT_SMALL, text_color=C["success"])
        self._report_status.pack(pady=16)

    def _export_pdf(self):
        history = self.db.get_history(self.current_user["id"])
        stats   = self.db.get_stats(self.current_user["id"])
        path    = report_generator.export_pdf(
            history, stats, self.current_user["username"])
        self._report_status.configure(text=f"✅ PDF saved: {os.path.basename(path)}")
        if mb.askyesno("Open Report", "PDF saved! Open it now?"):
            open_file(path)

    def _export_csv(self):
        history = self.db.get_history(self.current_user["id"])
        path    = report_generator.export_csv(history, self.current_user["username"])
        self._report_status.configure(text=f"✅ CSV saved: {os.path.basename(path)}")
        if mb.askyesno("Open File", "CSV saved! Open it now?"):
            open_file(path)

    def _export_excel(self):
        history = self.db.get_history(self.current_user["id"])
        path    = report_generator.export_excel(history, self.current_user["username"])
        self._report_status.configure(text=f"✅ Excel saved: {os.path.basename(path)}")
        if mb.askyesno("Open File", "Excel saved! Open it now?"):
            open_file(path)

    # ════════════════════════════════════════════════════════════════════
    # PAGE: Settings
    # ════════════════════════════════════════════════════════════════════
    def _build_settings(self, f: ctk.CTkFrame):
        hdr = ctk.CTkFrame(f, fg_color=C["panel"], corner_radius=0, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="⚙️ Settings",
                      font=FONT_TITLE, text_color=C["text"]).pack(side="left", padx=24, pady=16)

        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        # Appearance
        self._settings_section(scroll, "🎨 Appearance")
        ctk.CTkLabel(scroll, text="Appearance Mode", font=FONT_BODY,
                      text_color=C["text"]).pack(anchor="w", padx=8)
        mode_opt = ctk.CTkOptionMenu(
            scroll, values=["Dark", "Light", "System"],
            command=lambda m: ctk.set_appearance_mode(m))
        mode_opt.pack(anchor="w", padx=8, pady=(4, 14))

        # Account
        self._settings_section(scroll, "👤 Account")
        uname = self.current_user["username"]
        ctk.CTkLabel(scroll, text=f"Logged in as: {uname}",
                      font=FONT_BODY, text_color=C["muted"]).pack(anchor="w", padx=8, pady=4)
        ctk.CTkButton(scroll, text="Logout", height=38, width=140,
                       corner_radius=10, fg_color=C["danger"],
                       command=self._logout).pack(anchor="w", padx=8, pady=8)

        # About
        self._settings_section(scroll, "ℹ️ About")
        about_text = (
            "EmotionSense AI v1.0\n"
            "AI-Powered Emotion Detection & Mental Wellness Monitoring\n\n"
            "Technologies: customtkinter · VADER · TextBlob · Matplotlib · SQLite\n"
            "Optional: transformers · speechrecognition · reportlab · pandas\n\n"
            "Built for academic/portfolio demonstration purposes."
        )
        ctk.CTkLabel(scroll, text=about_text, font=FONT_SMALL,
                      text_color=C["muted"], justify="left").pack(anchor="w", padx=8)

    def _settings_section(self, parent, title: str):
        ctk.CTkLabel(parent, text=title, font=FONT_HEADING,
                      text_color=C["accent"]).pack(anchor="w", padx=8, pady=(16, 4))
        ctk.CTkFrame(parent, height=1, fg_color=C["border"]).pack(fill="x",
                                                                     padx=8, pady=(0, 8))

    # ── Auth ──────────────────────────────────────────────────────────────
    def _logout(self):
        self.current_user = None
        self._last_result = None
        for w in self.winfo_children():
            w.destroy()
        self._show_login()
