from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton
import sqlite3
import re
import random
from datetime import datetime

# ================== CONSTANTS ==================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

BAD_WORDS = [
    "fuck","shit","bitch","asshole","bastard",
    "mc","bc","madarchod","behenchod"
]

def censor(text):
    for w in BAD_WORDS:
        text = re.sub(rf"\b{w}\b", "%%", text, flags=re.I)
    return text

# ================== KIVY UI ==================
KV = '''
ScreenManager:
    LoginScreen:
    DashboardScreen:
    PublicNotesScreen:

<LoginScreen>:
    name: "login"
    MDBoxLayout:
        orientation: "vertical"
        padding: 40
        spacing: 20

        MDLabel:
            text: "Global Study"
            halign: "center"
            font_style: "H4"

        MDTextField:
            id: username
            hint_text: "Username"

        MDTextField:
            id: password
            hint_text: "Password"
            password: True

        MDRaisedButton:
            text: "Login"
            pos_hint: {"center_x": .5}
            on_release: app.login(username.text, password.text)

        MDRaisedButton:
            text: "Create Account"
            pos_hint: {"center_x": .5}
            on_release: app.signup(username.text, password.text)

<DashboardScreen>:
    name: "dash"
    MDBoxLayout:
        orientation: "vertical"

        MDToolbar:
            title: "Dashboard"

        MDScrollView:
            MDBoxLayout:
                orientation: "vertical"
                adaptive_height: True
                padding: 20
                spacing: 20

                MDTextField:
                    id: note_input
                    hint_text: "Write your note here"

                MDRaisedButton:
                    text: "Save Private Note"
                    on_release: app.save_private(note_input.text)

                MDRaisedButton:
                    text: "Publish Public Note"
                    on_release: app.publish_public(note_input.text)

                MDRaisedButton:
                    text: "View Public Notes"
                    on_release: app.show_public_notes()

                MDRaisedButton:
                    text: "Take Test"
                    on_release: app.take_test()

                MDRaisedButton:
                    text: "Logout"
                    on_release: app.logout()

<PublicNotesScreen>:
    name: "public"
    MDBoxLayout:
        orientation: "vertical"

        MDToolbar:
            title: "Public Notes"
            left_action_items: [["arrow-left", lambda x: app.back()]]

        MDScrollView:
            MDLabel:
                id: public_notes_label
                text: ""
                size_hint_y: None
                height: self.texture_size[1]
'''

# ================== SCREENS ==================
class LoginScreen(MDScreen): pass
class DashboardScreen(MDScreen): pass
class PublicNotesScreen(MDScreen): pass

# ================== APP ==================
class GlobalStudyApp(MDApp):

    def build(self):
        self.dialog = None
        self.conn = sqlite3.connect("global_study.db")
        self.cur = self.conn.cursor()

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            username TEXT PRIMARY KEY,
            password TEXT
        )""")

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS notes(
            username TEXT,
            content TEXT
        )""")

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS public_notes(
            username TEXT,
            content TEXT,
            created TEXT
        )""")

        self.conn.commit()

        # Ensure admin
        self.cur.execute("SELECT * FROM users WHERE username=?", (ADMIN_USERNAME,))
        if not self.cur.fetchone():
            self.cur.execute(
                "INSERT INTO users VALUES (?,?)",
                (ADMIN_USERNAME, ADMIN_PASSWORD)
            )
            self.conn.commit()

        self.current_user = None
        return Builder.load_string(KV)

    # ---------- AUTH ----------
    def login(self, u, p):
        self.cur.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (u, p)
        )
        if self.cur.fetchone():
            self.current_user = u
            self.root.current = "dash"
        else:
            self.show_dialog("Error", "Invalid login")

    def signup(self, u, p):
        if not u or not p:
            return
        try:
            self.cur.execute("INSERT INTO users VALUES (?,?)", (u, p))
            self.conn.commit()
            self.show_dialog("Success", "Account created")
        except:
            self.show_dialog("Error", "User already exists")

    def logout(self):
        self.current_user = None
        self.root.current = "login"

    # ---------- NOTES ----------
    def save_private(self, text):
        if not text:
            return
        self.cur.execute(
            "INSERT INTO notes VALUES (?,?)",
            (self.current_user, text)
        )
        self.conn.commit()
        self.show_dialog("Saved", "Private note saved")

    def publish_public(self, text):
        if not text:
            return
        text = censor(text)
        self.cur.execute(
            "INSERT INTO public_notes VALUES (?,?,?)",
            (self.current_user, text, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        self.conn.commit()
        self.show_dialog("Published", "Public note published")

    # ---------- VIEW PUBLIC ----------
    def show_public_notes(self):
        self.cur.execute(
            "SELECT username, content, created FROM public_notes ORDER BY created DESC"
        )
        notes = self.cur.fetchall()

        out = ""
        for u, c, d in notes:
            out += f"[b]{u}[/b] ({d})\n{c}\n\n"

        self.root.get_screen("public").ids.public_notes_label.text = out
        self.root.current = "public"

    def back(self):
        self.root.current = "dash"

    # ---------- TEST ----------
    def take_test(self):
        self.cur.execute(
            "SELECT content FROM notes WHERE username=?",
            (self.current_user,)
        )
        notes = [n[0] for n in self.cur.fetchall()]

        if not notes:
            self.show_dialog("No Notes", "Add notes first")
            return

        random.shuffle(notes)
        questions = notes[:10]
        score = len(questions) * 10

        self.show_dialog("Test Complete", f"Your Score: {score} / 100")

    # ---------- DIALOG ----------
    def show_dialog(self, title, text):
        if self.dialog:
            self.dialog.dismiss()
        self.dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(text="OK", on_release=lambda x: self.dialog.dismiss())
            ]
        )
        self.dialog.open()

# ================== RUN ==================
if __name__ == "__main__":
    GlobalStudyApp().run()
