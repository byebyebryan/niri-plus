#!/usr/bin/env python3
"""Render reference GTK3/Qt6 widgets on an owned Xvfb or offscreen backend."""
import argparse
import hashlib
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import time


def child(kind, family, target):
    if kind == "gtk":
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk, Pango
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-font-name", family + " 11")
        settings.set_property("gtk-application-prefer-dark-theme", True)
        settings.set_property("gtk-icon-theme-name", "breeze-dark")
        window = Gtk.OffscreenWindow()
        window.set_default_size(520, 330)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_border_width(24)
        window.add(box)
        title = Gtk.Label(label="Network connection")
        title.set_xalign(0)
        box.pack_start(title, False, False, 0)
        sub = Gtk.Label(label="GTK3 · adw-gtk3-dark · " + family + " 11pt")
        sub.set_xalign(0)
        box.pack_start(sub, False, False, 0)
        entry = Gtk.Entry()
        entry.set_text("Workshop Wi-Fi / 开发工作区")
        box.pack_start(entry, False, False, 0)
        toggle = Gtk.CheckButton(label="Connect automatically")
        toggle.set_active(True)
        box.pack_start(toggle, False, False, 0)
        progress = Gtk.ProgressBar()
        progress.set_fraction(0.65)
        box.pack_start(progress, False, False, 0)
        row = Gtk.Box(spacing=10)
        row.set_halign(Gtk.Align.END)
        for label in ["Cancel", "Connect"]:
            button = Gtk.Button(label=label)
            row.pack_start(button, False, False, 0)
        box.pack_end(row, False, False, 0)
        window.show_all()
        for _ in range(30):
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
            time.sleep(0.01)
        window.get_pixbuf().savev(target, "png", [], [])
        window.destroy()
        return {"style":"adw-gtk3-dark", "font":settings.get_property("gtk-font-name")}
    else:
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont, QFontInfo, QPalette, QColor
        from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QProgressBar, QPushButton, QStyleFactory
        app = QApplication([])
        styles = QStyleFactory.keys()
        chosen = next((x for x in styles if x.lower() == "breeze"), "Fusion")
        app.setStyle(chosen)
        app.setFont(QFont(family, 11))
        palette = QPalette()
        for role, color in [(QPalette.ColorRole.Window,"#1b1e20"),(QPalette.ColorRole.WindowText,"#fcfcfc"),(QPalette.ColorRole.Base,"#141618"),(QPalette.ColorRole.Text,"#fcfcfc"),(QPalette.ColorRole.Button,"#292c30"),(QPalette.ColorRole.ButtonText,"#fcfcfc"),(QPalette.ColorRole.Highlight,"#3daee9"),(QPalette.ColorRole.HighlightedText,"#fcfcfc")]:
            palette.setColor(role, QColor(color))
        app.setPalette(palette)
        window = QWidget()
        window.resize(520,330)
        box=QVBoxLayout(window);box.setContentsMargins(24,24,24,24);box.setSpacing(14)
        box.addWidget(QLabel("Network connection"))
        box.addWidget(QLabel("Qt6 · " + chosen + " / dark palette · " + family + " 11pt"))
        box.addWidget(QLineEdit("Workshop Wi-Fi / 开发工作区"))
        toggle=QCheckBox("Connect automatically");toggle.setChecked(True);box.addWidget(toggle)
        progress=QProgressBar();progress.setValue(65);box.addWidget(progress)
        box.addStretch()
        row=QHBoxLayout();row.addStretch()
        for label in ["Cancel","Connect"]:row.addWidget(QPushButton(label))
        box.addLayout(row);window.show();app.processEvents();window.grab().save(target);window.close()
        return {"style":chosen, "font":QFontInfo(app.font()).family()}


def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path);p.add_argument("--child",choices=["gtk","qt"]);p.add_argument("--font");p.add_argument("--target");args=p.parse_args()
    if args.child:
        print(json.dumps(child(args.child,args.font,args.target)));return
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    results=[]
    with tempfile.TemporaryDirectory(prefix="niri-native-reference-") as temp:
        scratch=Path(temp);(scratch/'runtime').mkdir(mode=0o700)
        display_file=scratch/'display'
        with display_file.open('w') as stream:
            xvfb=subprocess.Popen(['Xvfb','-displayfd',str(stream.fileno()),'-screen','0','800x600x24','-nolisten','tcp'],pass_fds=(stream.fileno(),),stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            for _ in range(100):
                if display_file.read_text().strip():break
                if xvfb.poll() is not None:raise RuntimeError('owned Xvfb failed')
                time.sleep(.05)
            display=':'+display_file.read_text().strip()
            for kind in ['gtk','qt']:
                for slug,font in [('inter','Inter Variable'),('noto','Noto Sans')]:
                    name=kind+'-'+slug+'.png'
                    env=dict(os.environ,DISPLAY=display,XDG_RUNTIME_DIR=str(scratch/'runtime'),XDG_CONFIG_HOME=str(scratch/'config'),XDG_CACHE_HOME=str(scratch/'cache'),XDG_STATE_HOME=str(scratch/'state'),GSETTINGS_BACKEND='memory',DBUS_SESSION_BUS_ADDRESS='unix:path='+str(scratch/'absent-bus'),GTK_THEME='adw-gtk3-dark',GDK_BACKEND='x11',QT_QPA_PLATFORM='offscreen',QT_QPA_PLATFORMTHEME='',QT_QPA_PLATFORMTHEME_QT6='',QT_SCALE_FACTOR='1',QT_FONT_DPI='96')
                    env.pop('WAYLAND_DISPLAY',None);env.pop('NIRI_SOCKET',None)
                    result=subprocess.run([sys.executable,__file__,'--child',kind,'--font',font,'--target',str(output/name)],env=env,capture_output=True,text=True,timeout=30)
                    if result.returncode:raise RuntimeError(result.stderr[-2000:])
                    results.append({'file':name,'sha256':hashlib.sha256((output/name).read_bytes()).hexdigest(),'toolkit':kind,'font':font+' 11pt','native_resolution':json.loads(result.stdout),'state':'isolated native reference, not selected theme or daily desktop','details':'GTK3 uses installed adw-gtk3-dark. Qt6 uses available Breeze/Fusion with a representative Breeze Dark palette.'})
        finally:
            xvfb.terminate()
            try:xvfb.wait(timeout=5)
            except subprocess.TimeoutExpired:xvfb.kill();xvfb.wait()
    (output/'native-provenance.json').write_text(json.dumps({'date':'2026-10-24','isolation':'Owned Xvfb, private XDG directories, no accessible session bus, Qt offscreen. No real network/audio/login actions.','samples':results,'limits':['Reference widgets are not SDDM/Gtklock/polkit or a complete native desktop preview.','Candidate-specific shell colors are explored in labeled HTML mockups; these show native styles and font feasibility.']},indent=2)+'\n')
    print(json.dumps({'native_reference_images':len(results)}))


if __name__=='__main__':main()
