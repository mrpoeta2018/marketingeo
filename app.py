import sys
import os
import time
s_sleep = time.sleep
import io
import random

# Forzar UTF-8 en la consola para evitar errores de caracteres
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def debug_log(msg):
    try:
        with open("DEBUG_STARTUP.txt", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except: pass
    print(f"[*] {msg}")

def speak(text):
    print(f"[VOZ] {text}")
    # Opcional: usar SAPI en Windows si est disponible
    try:
        import threading
        def _say():
            try:
                import win32com.client
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Speak(text)
            except: pass
        threading.Thread(target=_say, daemon=True).start()
    except: pass

# --- TEST DE VIDA INMEDIATO ---
print("\n" + "="*40)
print("OMNIUSB: INICIANDO MOTOR PYTHON...")
print("="*40)
print(f"[*] Carpeta: {os.getcwd()}")
print(f"[*] Python: {sys.version}")

try:
    import subprocess
    import traceback
    
    def log_error_and_die(err_msg):
        with open("LOG_CRITICO.txt", "w", encoding="utf-8") as f:
            f.write(f"=== ERROR CRÍTICO ===\n{err_msg}\n")
            traceback.print_exc(file=f)
        print(f"\n[X] ERROR: {err_msg}")
        input("\nPresiona ENTER para ver el error completo...")
        sys.exit(1)

    print("[*] Cargando librerías críticas...")
    import customtkinter as ctk
    import json
    import threading
    from tkinter import messagebox
    import requests
    
    print("[*] Cargando módulos internos...")
    from adb_manager import ADBManager
    from gnirehtet_runner import GnirehtetRunner
    from rotation_engine import RotationEngine
    from proxy_tester import ProxyTester
    from updater import check_for_updates_async, download_update, get_local_version
    from license_manager import get_hardware_id, validate_license
    from inventory_tool import InventoryWindow

except Exception as e:
    print(f"\n[!] FALLO CRÍTICO EN CARGA: {e}")
    traceback.print_exc()
    input("\nPresiona ENTER para cerrar...")
    sys.exit(1)

print("[*] Configurando interfaz visual...")
try:
    # Forzar modo oscuro directo evita que el módulo 'darkdetect' falle en PCs sin monitor (Headless/VPS)
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("green")
    # Forzar el escalado evita que Windows intente leer la resolución de un monitor inexistente
    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)
except Exception as e:
    print(f"[!] Error de tema visual (ignorado): {e}")

_ACCESS_PASSWORD = "Androide10"

class LicenseValidationWindow(ctk.CTkToplevel):
    def __init__(self, master, on_success_callback):
        super().__init__(master)
        self.title("🔒 Marketingeo - Activación de Licencia")
        self.geometry("500x380")
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.resizable(False, False)
        
        self.on_success = on_success_callback
        self.hwid = get_hardware_id()
        
        # UI
        ctk.CTkLabel(self, text="Verificación de Licencia", font=("Arial", 22, "bold"), text_color="#F59E0B").pack(pady=(20, 5))
        ctk.CTkLabel(self, text="Software v4.1 - Protegido por HWID", font=("Arial", 12)).pack(pady=5)
        
        frame = ctk.CTkFrame(self, corner_radius=10)
        frame.pack(padx=30, pady=10, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="🔑 Tu Código de Máquina (HWID):", font=("Arial", 12, "bold")).pack(pady=(15, 0))
        h_entry = ctk.CTkEntry(frame, width=200, justify="center")
        h_entry.pack(pady=5)
        h_entry.insert(0, self.hwid)
        h_entry.configure(state="readonly")
        
        ctk.CTkLabel(frame, text="🗝️ Introduce tu Licencia de Alquiler:", font=("Arial", 12, "bold")).pack(pady=(15, 0))
        self.key_entry = ctk.CTkEntry(frame, width=300, justify="center", placeholder_text="Ej: LIC-PABLO-1X9A")
        self.key_entry.pack(pady=5)
        
        self.status_lbl = ctk.CTkLabel(frame, text="", font=("Arial", 12))
        self.status_lbl.pack(pady=5)
        
        self.btn = ctk.CTkButton(self, text="Verificar y Entrar", fg_color="#10B981", height=40, font=("Arial", 14, "bold"), command=self.do_verify)
        self.btn.pack(pady=20, padx=30, fill="x")

    def on_close(self):
        sys.exit(0)

    def do_verify(self):
        k = self.key_entry.get().strip()
        if not k:
            self.status_lbl.configure(text="❌ Escribe una licencia.", text_color="red")
            return
            
        self.btn.configure(text="Comprobando...", state="disabled")
        self.status_lbl.configure(text="Conectando al servidor central...", text_color="yellow")
        
        def _check():
            ok, msg = validate_license(k, self.hwid)
            if not self.winfo_exists(): return
            
            self.btn.configure(text="Verificar y Entrar", state="normal")
            if ok:
                self.status_lbl.configure(text=msg, text_color="green")
                self.after(500, lambda: self.on_success(k))
            else:
                self.status_lbl.configure(text=msg, text_color="red")
                
        threading.Thread(target=_check, daemon=True).start()


class ReporteGlobalWindow(ctk.CTkToplevel):
    def __init__(self, master, adb, engine):
        super().__init__(master)
        self.title("🩺 Diagnóstico Global del Lote Activo")
        self.geometry("500x400")
        self.attributes("-topmost", True)
        
        self.adb = adb
        self.engine = engine
        
        ctk.CTkLabel(self, text="Verificando Conexiones en Curso...", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.log_box = ctk.CTkTextbox(self, width=450, height=300)
        self.log_box.pack(pady=10)
        
        threading.Thread(target=self.run_report, daemon=True).start()

    def run_report(self):
        activos = self.engine.active_devices.copy()
        if not activos:
            self.log_box.insert("end", "⚠️ No hay ningún celular activo en este momento.")
            return
            
        self.log_box.insert("end", f"[*] Escaneando salida de {len(activos)} celulares...\n\n")
        
        for dev in activos:
            s = dev['serial']
            cfg, ip = self.adb.get_real_ip(s)
            state = "🟢 OK" if "MUERTO" not in ip and "SIN" not in ip else "🔴 FALLA"
            self.log_box.insert("end", f"{state} | {s}\n   └─ {cfg}\n   └─ {ip}\n\n")
            self.log_box.see("end")

class ProxyTesterWindow(ctk.CTkToplevel):
    def __init__(self, master, proxies, callback_finish):
        super().__init__(master)
        self.title("🔍 Probador Láser de Proxies")
        self.geometry("600x450")
        self.attributes("-topmost", True)
        self.proxies = proxies
        self.callback_finish = callback_finish
        
        ctk.CTkLabel(self, text="Escaneando Proxies en Paralelo...", font=("Arial", 16, "bold")).pack(pady=10)
        self.progress = ctk.CTkProgressBar(self, width=500)
        self.progress.pack(pady=10)
        self.progress.set(0.0)
        
        self.status = ctk.CTkLabel(self, text="Verificando 0 / 0")
        self.status.pack(pady=5)
        
        self.log_box = ctk.CTkTextbox(self, width=550, height=250)
        self.log_box.pack(pady=10)
        
        threading.Thread(target=self.run_test, daemon=True).start()
        
    def add_log(self, text, color="white"):
        def _do():
            if not self.winfo_exists(): return
            self.log_box.insert("end", text + "\n")
            self.log_box.see("end")
        self.after(0, _do)

    def log_update(self, c, total, p, is_alive):
        def _do():
            if not self.winfo_exists(): return
            self.progress.set(c / total)
            self.status.configure(text=f"Verificados {c} de {total}")
            res = "🟢 VIVO" if is_alive else "🔴 MUERTO"
            self.log_box.insert("end", f"{res} | {p}\n")
            self.log_box.see("end")
        self.after(0, _do)
        
    def run_test(self):
        def _final(results):
            def _do():
                if not self.winfo_exists(): return
                a = len(results["alive"])
                d = len(results["dead"])
                self.log_box.insert("end", f"\n--- PRUEBA FINALIZADA ---\n✅ Vivos: {a}\n💥 Muertos: {d}\nLimpiando lista automáticamente en 3 segundos...\n")
                self.log_box.see("end")
            self.after(0, _do)
            time.sleep(3)
            self.after(0, lambda: self.callback_finish(results["alive"]))
            self.after(0, self.destroy)
            
        ProxyTester.test_proxies_async(self.proxies, self.log_update, _final)

class PanicProgressWindow(ctk.CTkToplevel):
    def __init__(self, master, engine, runner, adb):
        super().__init__(master)
        self.title("🧹 Limpieza Global en Progreso...")
        self.geometry("550x450")
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        
        self.master = master
        self.engine = engine
        self.runner = runner
        self.adb = adb
        
        ctk.CTkLabel(self, text="EJECUTANDO PROTOCOLO PANIC", text_color="red", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.pack(pady=10)
        self.progress.set(0.0)
        
        self.status_box = ctk.CTkTextbox(self, width=450, height=200)
        self.status_box.pack(pady=10)
        self.status_box.insert("end", "[X] Escaneando procesos...\n")
        
        threading.Thread(target=self.run_cleanup, daemon=True).start()

    def log(self, text):
        def _do():
            if not self.winfo_exists(): return
            self.status_box.insert("end", text + "\n")
            self.status_box.see("end")
        self.after(0, _do)

    def do_nothing(self): pass
        
    def run_cleanup(self):
        time.sleep(1)
        self.progress.set(0.2)
        
        self.log("[✓] Deteniendo motor rotante...")
        self.engine.stop_rotation()
        time.sleep(1)
        
        self.progress.set(0.4)
        self.log("[✓] Deteniendo todos los Gnirehtet del PC...")
        self.runner.kill_all_gnirehtet()
        
        try:
            self.log("[✓] Destruyendo servidores NodeProxy...")
            self.engine.pm.stop_all()
        except: pass
        self.progress.set(0.6)
        
        devices = self.adb.list_devices()
        total = len(devices)
        success_count = 0
        failed_devices = []
        if total == 0:
            self.progress.set(0.9)
        else:
            self.log(f"[✓] Apagando Wi-Fi en todos los celulares preventivamente...")
            for dev in devices:
                self.adb.run_command(["shell", "svc", "wifi", "disable"], dev['serial'])
                
            self.log(f"[✓] Verificando red 1 por 1 en {total} celulares...")
            success_count = 0
            failed_devices = []
            
            for i, dev in enumerate(devices):
                s = dev['serial']
                self.log(f"\n-> Limpiando y probando {s} ({i+1}/{total})...")
                
                self.runner.stop(s)
                self.adb.run_command(["shell", "am", "start", "-a", "com.genymobile.gnirehtet.STOP", "-n", "com.genymobile.gnirehtet/.GnirehtetActivity"], s)
                self.adb.run_command(["uninstall", "com.genymobile.gnirehtet"], s)
                self.adb.clear_global_proxy(s)
                self.adb.run_command(["shell", "settings", "put", "global", "captive_portal_mode", "0"], s)
                self.adb.run_command(["shell", "settings", "put", "global", "captive_portal_detection_enabled", "0"], s)
                self.adb.run_command(["reverse", "--remove-all"], s)
                
                self.adb.run_command(["shell", "svc", "wifi", "enable"], s)
                
                internet_ok = False
                for attempt in range(5):
                    time.sleep(2)
                    stdout, stderr, code = self.adb.run_command(["shell", "ping", "-c", "1", "-W", "2", "8.8.8.8"], s)
                    if code == 0:
                        internet_ok = True
                        break
                        
                if internet_ok:
                    self.log(f"   [✅] INTERNET OK. Abriendo Google...")
                    self.adb.run_command(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", "https://www.google.com"], s)
                    time.sleep(2)
                    success_count += 1
                else:
                    self.log(f"   [❌] FALLO. No se pudo conectar a Internet.")
                    failed_devices.append(s)
                    
                self.adb.run_command(["shell", "svc", "wifi", "disable"], s)
                
                p = 0.6 + (0.3 * ((i+1)/total))
                self.after(0, lambda val=p: self.progress.set(val) if self.winfo_exists() else None)

        self.after(0, lambda: self.progress.set(1.0) if self.winfo_exists() else None)
        self.log(f"\n✅ ¡PANIC COMPLETADO! Se probaron {total} celulares.")
        self.log(f"🟢 Exitosos: {success_count} | 🔴 Fallidos: {len(failed_devices)}")
        if failed_devices:
            self.log(f"Revisar manual: {', '.join(failed_devices)}")
        self.log("⚠️ NOTA: El Wi-Fi quedó APAGADO. Actívalo manualmente.")
        
        self.after(0, lambda: self.master.log_msg("Protocolo a prueba de fallos finalizado.", "warn"))
        self.after(0, lambda: self.master.status_lbl.configure(text="Estado: LIMPIO 🧽"))
        self.after(0, lambda: self.master.start_btn.configure(state="normal"))
        self.after(0, lambda: self.master.pause_btn.configure(state="disabled", text="⏸️ PAUSAR"))
        self.after(0, lambda: self.master.clean_btn.configure(state="normal"))
        
        # Restore close button and auto-destroy after 3 seconds
        self.after(0, lambda: self.protocol("WM_DELETE_WINDOW", self.destroy))
        def _add_btn():
            if not self.winfo_exists(): return
            btn = ctk.CTkButton(self, text="Cerrar Ventana", command=self.destroy, fg_color="#EF4444")
            btn.pack(pady=10)
        self.after(0, _add_btn)
        self.after(3000, self.destroy)

class ScanProgressWindow(ctk.CTkToplevel):
    def __init__(self, master, adb_manager, finish_cb):
        super().__init__(master)
        self.title("🔍 Escaneando Dispositivos")
        self.geometry("500x350")
        self.attributes("-topmost", True)
        
        self.master = master
        self.adb = adb_manager
        self.finish_cb = finish_cb
        
        ctk.CTkLabel(self, text="RECONOCIENDO HARDWARE", text_color="#F59E0B", font=("Arial", 16, "bold")).pack(pady=15)
        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.set(0.1)
        self.progress.pack(pady=10)
        
        self.status_lbl = ctk.CTkLabel(self, text="Enviando señales ADB...")
        self.status_lbl.pack(pady=5)
        
        self.tip_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        self.tip_frame.pack(fill="x", padx=25, pady=20)
        self.tip_lbl = ctk.CTkLabel(self.tip_frame, text=self.master.tips[0], wraplength=450)
        self.tip_lbl.pack(pady=10)
        
        threading.Thread(target=self.run_scan, daemon=True).start()

    def _safe_lbl(self, txt):
        try:
            if self.winfo_exists(): self.status_lbl.configure(text=txt)
        except: pass

    def _safe_prog(self, val):
        try:
            if self.winfo_exists(): self.progress.set(val)
        except: pass

    def run_scan(self):
        self.after(0, lambda: self._safe_prog(0.3))
        self.after(500, lambda: self._safe_lbl("Esperando respuesta de hubs USB..."))
        devs = self.adb.list_devices()
        self.after(0, lambda: self._safe_prog(0.8))
        self.after(500, lambda: self._safe_lbl(f"📱 Encontrados {len(devs)} teléfonos!"))
        import time
        time.sleep(1)
        try:
            if self.winfo_exists():
                self.after(0, self.finish_cb, devs)
                self.after(0, self.destroy)
        except: pass

class SetupProgressWindow(ctk.CTkToplevel):
    def __init__(self, master, devices, proxies, b_size, mins, tunnel_disabled=False):
        super().__init__(master)
        self.title("🚀 Iniciando Granja de Proxies")
        self.geometry("600x480")
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        
        self.master = master
        self.devices = devices
        self.proxies = proxies
        self.b_size = b_size
        self.mins = mins
        self.tunnel_disabled = tunnel_disabled
        
        if tunnel_disabled:
            ctk.CTkLabel(self, text="MODO SOLO BOT (WIFI ACTIVO)", text_color="#FCD34D", font=("Arial", 18, "bold")).pack(pady=15)
        else:
            ctk.CTkLabel(self, text="MODO ARRANQUE ACTIVO", text_color="#F59E0B", font=("Arial", 18, "bold")).pack(pady=15)
        
        self.progress = ctk.CTkProgressBar(self, width=500)
        self.progress.pack(pady=10)
        self.progress.set(0.05)
        
        self.status_lbl = ctk.CTkLabel(self, text="Inicializando componentes...", font=("Arial", 12, "italic"))
        self.status_lbl.pack(pady=5)
        
        self.log_box = ctk.CTkTextbox(self, width=550, height=200)
        self.log_box.pack(pady=10)
        
        self.tip_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        self.tip_frame.pack(fill="x", padx=25, pady=10)
        self.tip_lbl = ctk.CTkLabel(self.tip_frame, text=self.master.tips[0], wraplength=500)
        self.tip_lbl.pack(pady=10)
        
        self.disable_master_buttons()
        threading.Thread(target=self.run_setup, daemon=True).start()
        threading.Thread(target=self.rotate_tips, daemon=True).start()

    def do_nothing(self): pass

    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def disable_master_buttons(self):
        self.master.start_btn.configure(state="disabled")
        self.master.scan_btn.configure(state="disabled")
        self.master.install_btn.configure(state="disabled")
        self.master.clean_btn.configure(state="disabled")

    def enable_master_buttons(self):
        self.master.start_btn.configure(state="disabled") # starts stays off while running
        self.master.scan_btn.configure(state="normal") 
        self.master.clean_btn.configure(state="normal")

    def rotate_tips(self):
        while self.winfo_exists():
            time.sleep(6)
            if self.winfo_exists():
                self.after(0, lambda: self.tip_lbl.configure(text=random.choice(self.master.tips)))

    def run_setup(self):
        self.log("[*] Paso 1: Iniciando y validando dependencias...")
        self.status_lbl.configure(text="Iniciando entorno local (Previene errores de red)...")
        if not self.tunnel_disabled:
            self.master.engine.pm.download_if_missing()
        self.progress.set(0.2)
        time.sleep(1)
        
        if self.tunnel_disabled:
            self.log("[*] Paso 2: (Saltado) Modo Solo Bot activado. Manteniendo Wi-Fi activo.")
            self.progress.set(0.5)
            self.log("[*] Paso 3: Configurando Rotación Lógica...")
            self.status_lbl.configure(text="Iniciando motores lógicos...")
        else:
            self.log("[*] Paso 2: Desactivando Wi-Fi escalonadamente (Previene saturación del Hub USB)...")
            threads = []
            total = len(self.devices)
            for i, d in enumerate(self.devices):
                def _kill(serial=d['serial']):
                    self.master.adb.run_command(["shell", "svc", "wifi", "disable"], serial)
                    self.master.adb.run_command(["shell", "settings", "put", "system", "accelerometer_rotation", "0"], serial)
                t = threading.Thread(target=_kill)
                t.start()
                threads.append(t)
                self.progress.set(0.2 + (0.3 * ((i+1)/total)))
                self.status_lbl.configure(text=f"Desconectando Wi-Fi (Protegiendo Hardware) {i+1}/{total}...")
            
            for t in threads: t.join()
            self.log("[✓] Hardware seguro: Wi-Fi bloqueado en todos los dispositivos.")
            
            self.log("[*] Paso 3: Configurando Túneles y Proxies (Pausando para no crashear ADB)...")
            self.status_lbl.configure(text="Inyectando túneles ADB Reverse de forma segura...")
        
        self.progress.set(0.6)
        
        # Start rotation on main thread via after
        playlists = []
        
        self.after(0, lambda: self.master.engine.start_rotation(
            self.devices, self.proxies, self.b_size, self.mins, 
            True, False, playlists, tunnel_disabled=self.tunnel_disabled
        ))
        
        self.progress.set(0.9)
        time.sleep(2)
        self.progress.set(1.0)
        self.log("\n✅ ¡SISTEMA OPERATIVO Y PROTEGIDO!")
        self.status_lbl.configure(text="Lanzamiento completado con éxito.")
        
        self.enable_master_buttons()
        # Restore close button and add button
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        btn = ctk.CTkButton(self, text="Perfecto, Continuar", command=self.destroy, fg_color="#10B981")
        btn.pack(pady=10)
        self.after(4000, self.destroy)

class ProxyAssignmentWindow(ctk.CTkToplevel):
    def __init__(self, master, devices, proxies):
        super().__init__(master)
        self.title("🎯 Mapeado Manual de Proxies")
        self.geometry("800x600")
        self.attributes("-topmost", True)
        
        self.master = master
        self.devices = devices
        self.proxies = proxies # Formatted list
        self.entries = {} # serial -> StringVar
        
        ctk.CTkLabel(self, text="ASIGNACIÓN DISPOSITIVO <-> PROXY", font=("Arial", 20, "bold"), text_color="#F59E0B").pack(pady=20)
        
        # Scrollable area
        self.scroll = ctk.CTkScrollableFrame(self, width=750, height=400)
        self.scroll.pack(padx=20, pady=10, fill="both", expand=True)
        
        for dev in self.devices:
            s = dev['serial']
            row = ctk.CTkFrame(self.scroll, fg_color="#1E1E1E", corner_radius=5)
            row.pack(fill="x", pady=2, padx=5)
            
            ctk.CTkLabel(row, text=f"{dev.get('model','Phone')} ({s})", width=250, anchor="w").pack(side="left", padx=10)
            
            p_var = ctk.StringVar(value=self.master.engine.custom_mapping.get(s, ""))
            self.entries[s] = p_var
            
            combo = ctk.CTkComboBox(row, values=["(Automático)"] + self.proxies, variable=p_var, width=400)
            combo.pack(side="left", padx=10, pady=5)

        # Buttons
        btn_fr = ctk.CTkFrame(self, fg_color="transparent")
        btn_fr.pack(pady=20)
        
        ctk.CTkButton(btn_fr, text="🎲 Mapeado Automático (1 a 1)", command=self.auto_map, fg_color="#F59E0B").pack(side="left", padx=10)
        ctk.CTkButton(btn_fr, text="💾 Guardar Mapeado", command=self.save_map, fg_color="#10B981").pack(side="left", padx=10)
        ctk.CTkButton(btn_fr, text="❌ Limpiar Todo", command=self.clear_map, fg_color="#EF4444").pack(side="left", padx=10)

    def auto_map(self):
        for i, s in enumerate(self.entries.keys()):
            if i < len(self.proxies):
                self.entries[s].set(self.proxies[i])
            else:
                self.entries[s].set("(Automático)")

    def clear_map(self):
        for var in self.entries.values():
            var.set("(Automático)")

    def save_map(self):
        new_map = {}
        for s, var in self.entries.items():
            val = var.get()
            if val and val != "(Automático)":
                new_map[s] = val
        self.master.engine.custom_mapping = new_map
        self.master.log_msg(f"🎯 Mapeado guardado: {len(new_map)} dispositivos asignados manualmente.")
        self.destroy()

class MarketingeoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("OmniUSB Director 🌍 [Stealth Proxy Edition]")
        self.geometry("1200x900")
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        print("[*] Iniciando ADB y Gnirehtet...")
        debug_log("Creando instancia ProxyFarmApp")
        speak("Cargando componentes de red")
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.adb = ADBManager(os.path.join(base_dir, "platform-tools", "adb.exe"))
        self.runner = GnirehtetRunner(executable_path=os.path.join(base_dir, "gnirehtet.exe"))
        debug_log("Motores ADB/Runner listos")
        self.engine = RotationEngine(self.adb, self.runner, self.on_update_callback if hasattr(self, "on_update_callback") else self.on_engine_update, app_instance=self)
        
        self.no_proxy_strikes = 0
        self.scanned_devices = []  # Stores last scan results
        self.device_selections = {}  # serial -> BooleanVar (checkbox state)
        self.is_compact = False  # Compact mode state
        self.bot_enabled = ctk.BooleanVar(value=False)
        self.bot_interval = ctk.StringVar(value="5")
        self.device_locks = {} # serial -> timestamp (until when is it busy)

        # Master Rotation State
        self.master_mode = ctk.StringVar(value="spotify") # "spotify", "youtube", "mixed"
        self.master_mode.trace_add("write", lambda *args: self.update_ui_state())
        self.mixed_turn = "spotify"

        self.media_rotation_active = ctk.BooleanVar(value=False) # Media Injection On/Off
        
        # Obsolete network rotation state
        self.network_rotation_enabled = ctk.BooleanVar(value=False)
        self.network_rotation_enabled.trace_add("write", lambda *args: self.update_ui_state())

        # Interval states
        self.playlist_interval = ctk.StringVar(value="60") # in minutes
        self.next_injection_time = time.time()
        
        self.youtube_drip_var = ctk.BooleanVar(value=True) # Human Drip Mode
        
        # Anti-Bot Shield (Watchdog & Ghost)
        self.watchdog_enabled = ctk.BooleanVar(value=True)
        self.ghost_enabled = ctk.BooleanVar(value=True)

        # Handle window close: cleanup all processes
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=5, padx=10)
        title = ctk.CTkLabel(self.header_frame, text="🛸 Marketingeo Panel Central", font=("Arial", 22, "bold"))
        title.pack(side="left", padx=10)
        self.compact_btn = ctk.CTkButton(self.header_frame, text="📏 Compacto", width=100, height=28, command=self.toggle_compact, fg_color="#374151", hover_color="#4B5563")
        self.compact_btn.pack(side="left", padx=10)
        self.status_lbl = ctk.CTkLabel(self.header_frame, text="Estado: ESPERANDO... 🌙", text_color="yellow")
        self.status_lbl.pack(side="right", padx=10)
        self.update_status_lbl = ctk.CTkLabel(self.header_frame, text="🔍 Buscando actualizaciones...", text_color="#9CA3AF")
        self.update_status_lbl.pack(side="right", padx=15)
        
        self.tabview = ctk.CTkTabview(self, width=1150, height=800)
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)
        self.tab_ctrl = self.tabview.add(" Panel de Control (ADB/Proxys)")
        self.tab_social = self.tabview.add(" Mdulo Kick")
        self.tab_ig = self.tabview.add(" Mdulo Instagram")
        self.tab_accounts = self.tabview.add(" Creador de Cuentas")
        self.tab_labs = self.tabview.add(" Laboratorio (Prximas Redes)")

        # Global Log Frame
        self.log_frame = ctk.CTkTextbox(self, height=120)
        self.log_frame.pack(padx=20, pady=(0, 10), fill="x")
        self.log_frame.configure(state="disabled")
        
        self.batch_size_sync_id = None
        self.tips = [
            "💡 Consejo: Activa 'Modo Sigilo (Goteo)' si usas proxies móviles para evitar baneos simultáneos.",
            "💡 Consejo: Revisa la luz de salud. Si está Naranja, el sistema se estabilizará solo.",
            "💡 Consejo: Entra a WhatsApp o Instagram directo desde el celular usando SCRCPY ('Pantalla')."
        ]

        self.last_ip_check = {}
        self.device_health = {}
        self.health_fail_count = {}

        # Iniciar visible para evitar error de "ventana escondida" en algunas PCs
        print("[*] Cargando Interfaz Principal...")
        # self.withdraw() # Comentado para estabilidad
        self.check_saved_license_and_boot()

    def check_saved_license_and_boot(self):
        debug_log("Saltando comprobación de licencia a petición del usuario...")
        self.after(0, self._finalize_boot, "FREE_VERSION")

    def _show_license_window(self):
        LicenseValidationWindow(self, self._finalize_boot)

    def bind_tooltip(self, widget, text):
        import tkinter as tk
        def on_enter(e):
            widget.tooltip_window = tk.Toplevel(widget)
            widget.tooltip_window.wm_overrideredirect(True)
            # Posicionar el tooltip un poco a la derecha y abajo del cursor
            widget.tooltip_window.wm_geometry(f"+{e.x_root + 15}+{e.y_root + 15}")
            widget.tooltip_window.attributes("-topmost", True)
            
            # Usar un Frame de tkinter nativo o un label nativo para que se adapte al Toplevel limpio,
            # pero como es Toplevel, CTkLabel funciona perfectamente.
            label = ctk.CTkLabel(widget.tooltip_window, text=text, font=("Arial", 12, "bold"), fg_color="#1E293B", text_color="#FCD34D", corner_radius=6)
            # El padding en CTkLabel se maneja en el pack o pasándole height/width, pero padx/pady en pack funciona.
            label.pack(padx=10, pady=5)
            
        def on_leave(e):
            if hasattr(widget, 'tooltip_window') and widget.tooltip_window:
                widget.tooltip_window.destroy()
                widget.tooltip_window = None
                
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def lock_device(self, serial, duration_seconds=40):
        self.device_locks[serial] = time.time() + duration_seconds

    def is_device_locked(self, serial):
        if serial not in self.device_locks:
            return False
        return time.time() < self.device_locks[serial]

    def _finalize_boot(self, valid_key):
        debug_log("Finalizando arranque...")
        speak("Acceso concedido. Abriendo panel de control.")
        # Guardar clave válida
        try:
            doc = {}
            if os.path.exists("config.json"):
                with open("config.json", "r") as f: doc = json.load(f)
            doc["license_key"] = valid_key
            with open("config.json", "w") as f: json.dump(doc, f)
        except: pass
        self.build_control_tab()
        self.build_social_tab() # Now Kick
        self.build_ig_tab()
        self.build_accounts_tab()
        self.build_labs_tab()

        self.deiconify()
        print("[+] ¡Interfaz Abierta con Éxito!")
        self.log_msg("✅ Sistema iniciado. Bienvenido.")
        
        self.load_config()
        self.tips = [
            "💡 TIP: Asegúrate de usar cables USB de buena calidad para los 40 móviles.",
            "💡 TIP: Si un teléfono falla, revisa que no tenga un aviso de 'Permitir depuración' en pantalla.",
            "💡 TIP: El icono de llave 🔑 debe aparecer en la barra de estado de los celulares.",
            "💡 TIP: No desconectes el HUB USB mientras el túnel esté activo.",
            "💡 TIP: Puedes ver el consumo de cada móvil en la pestaña 'Tráfico en Vivo'."
        ]
        
        self.device_ui_map = {} # serial -> {ip_lbl, timer_lbl, traffic_lbl, health_lbl}
        self.device_health = {} # serial -> {status: "ok"|"warning"|"dead"|"offline", reason: str}
        self.health_fail_count = {} # serial -> consecutive failure count
        self.last_ip_check = {} # serial -> timestamp
        self.update_bar = None  # Update notification bar
        self.update_timer()
        self.update_traffic()
        self._check_updates()
        if True:
            pass
            
            
            

    def toggle_compact(self):
        """Alterna entre modo completo y modo bolsillo (solo controles)."""
        if self.is_compact:
            # Restaurar modo completo
            self.is_compact = False
            ctk.set_widget_scaling(1.0)
            self.geometry("1200x900")
            self.compact_btn.configure(text="📏 Bolsillo")
            self._right_container.grid(row=1, column=1, pady=10, padx=10, sticky="nsew")
            self.log_frame.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky="ew")
            self.proxy_textbox.configure(height=120)
            self.tab_ctrl.grid_columnconfigure(1, weight=1)
        else:
            # Modo bolsillo: solo columna de controles, sin log ni tarjetas
            self.is_compact = True
            ctk.set_widget_scaling(0.77)
            self.geometry("480x700")
            self.compact_btn.configure(text="📐 Completo")
            self._right_container.grid_remove()
            self.log_frame.grid_remove()
            self.proxy_textbox.configure(height=50)
            self.tab_ctrl.grid_columnconfigure(1, weight=0)

    def _check_updates(self):
        """Check for updates in background on startup."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        git_dir = os.path.join(base_dir, ".git")
        
        # Verificar si Git está disponible en la PC y configurado
        git_available = False
        try:
            import subprocess
            subprocess.run(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            git_available = True
        except:
            pass
            
        if not os.path.exists(git_dir) or not git_available:
            self.update_status_lbl.configure(text="⚠️ Sin Git (Actualización desactivada)", text_color="#F59E0B")
            return
            
        def _on_result(has_update, remote_info):
            if has_update and remote_info:
                self.after(0, lambda: self.update_status_lbl.configure(text="🚀 Nueva actualización!", text_color="#10B981"))
                self.after(0, self._show_update_bar, remote_info)
            else:
                self.after(0, lambda: self.update_status_lbl.configure(text=f"✅ App al día (v{get_local_version().get('version', '?')})", text_color="#F59E0B"))
                
        check_for_updates_async(_on_result)

    def _show_update_bar(self, remote_info):
        """Show a subtle update notification bar at the top."""
        local = get_local_version()
        self.update_bar = ctk.CTkFrame(self, fg_color="#065F46", corner_radius=0, height=36)
        self.update_bar.pack(fill="x", before=self.tabview)
        ctk.CTkLabel(self.update_bar, text=f"🆕 Nueva versión {remote_info.get('version', '?')} disponible (actual: {local.get('version', '?')})", font=("Arial", 12, "bold")).pack(side="left", padx=15)
        download_url = remote_info.get("download_url", "")
        if download_url:
            ctk.CTkButton(self.update_bar, text="⬇️ Actualizar", width=120, height=26, fg_color="#10B981",
                          command=lambda: self._do_update(download_url)).pack(side="right", padx=10, pady=5)
        ctk.CTkButton(self.update_bar, text="✕", width=30, height=26, fg_color="transparent",
                      command=self.update_bar.destroy).pack(side="right", padx=5, pady=5)

    def _do_update(self, url):
        """Download and install update."""
        self.log_msg("⬇️ Descargando actualización...", "warn")
        def _progress(msg):
            self.after(0, lambda: self.log_msg(f"  {msg}"))
        def _done(success, msg):
            if success:
                self.after(0, lambda: self.log_msg(f"✅ {msg}"))
                self.after(0, lambda: messagebox.showinfo("Actualización", f"{msg}\nCierra y vuelve a abrir START_APP.bat"))
            else:
                self.after(0, lambda: self.log_msg(f"❌ {msg}", "error"))
        download_update(url, _progress, _done)

    def on_close(self):
        """Clean up all child processes before closing the window."""
        try:
            self.engine.stop_rotation()
            self.runner.kill_all_gnirehtet()
            self.engine.pm.stop_all()
        except Exception:
            pass
        self.destroy()


    def update_live_status(self):
        try:
            if not hasattr(self, 'media_rotation_active'): return
            if not self.media_rotation_active.get():
                self.live_status_var.set("Estado: ⏸️ INYECCIÓN AUTOMÁTICA APAGADA")
                return
                
            mode = self.master_mode.get()
            mode_str = mode
            if mode == "spotify": mode_str = "🟢 SOLO SPOTIFY"
            elif mode == "yt_music": mode_str = "🟣 SOLO YT MUSIC"
            elif mode == "yt_video": mode_str = "🔴 SOLO YT VIDEO"
            elif mode == "mixed": 
                # Add sub-state if mixed
                sub = getattr(self, '_last_mixed_mode', None)
                if sub == "spotify": mode_str = "🟡 MIXTO -> 🟢 Spotify"
                elif sub == "yt_music": mode_str = "🟡 MIXTO -> 🟣 YT Music"
                elif sub == "yt_video": mode_str = "🟡 MIXTO -> 🔴 YT Video"
                else: mode_str = "🟡 MODO MIXTO"
            
            shield_active = self.watchdog_enabled.get() or self.ghost_enabled.get() or self.bot_enabled.get()
            shield_str = "🛡️ ON" if shield_active else "⚠️ OFF"
            
            if getattr(self, 'is_injecting', False):
                self.live_status_var.set(f"Estado: {mode_str} | Próxima inyección: ⏳ INYECTANDO... | Escudo: {shield_str}")
            else:
                remaining = int(self.next_injection_time - time.time())
                if remaining < 0: remaining = 0
                mins, secs = divmod(remaining, 60)
                time_str = f"{mins:02d}:{secs:02d}"
                self.live_status_var.set(f"Estado: {mode_str} | Próxima inyección: ⏱️ {time_str} | Escudo: {shield_str}")
        except:
            pass








    def _cleanup_background_apps(self, serial, exclude_pkg=None):
        pkgs = ["com.android.chrome", "com.spotify.music", "com.google.android.youtube", "com.google.android.apps.youtube.music", 
                "com.pandora.android", "fm.awa.app", "com.audiomack", "com.aspiro.tidal", "com.apple.android.music", "com.amazon.mp3",
                "com.instagram.android", "com.kick.mobile"]
        for pkg in pkgs:
            if pkg != exclude_pkg:
                self.adb.run_command(["shell", "am", "force-stop", pkg], serial)






















    def install_custom_apk(self):
        """Abre un dialogo para buscar un APK y lo instala en todos los dispositivos."""
        if not hasattr(self, 'engine') or not getattr(self.engine, 'active_devices', []):
            self.log_msg(" [Error] No hay dispositivos activos en el panel.", "error")
            return
            
        import tkinter.filedialog as fd
        import threading
        
        filepath = fd.askopenfilename(title="Seleccionar APK a Instalar (Kick, Instagram...)", filetypes=[("APK files", "*.apk")])
        if not filepath:
            return
            
        filename = os.path.basename(filepath)
        self.log_msg(f" Preparando para instalar: {filename}...", "info")
        
        if hasattr(self, 'install_apk_btn'):
            self.install_apk_btn.configure(text=" ⏳ Instalando...", state="disabled", fg_color="#F59E0B")
            
        def _installer():
            from concurrent.futures import ThreadPoolExecutor
            
            def install_on_dev(dev):
                s = dev['serial']
                self.log_msg(f" [{s[-4:]}] Instalando {filename}...", "info")
                # -r: replace existing, -g: grant all runtime permissions
                out, err, code = self.adb.run_command(["install", "-r", "-g", filepath], s)
                if code == 0 and "Success" in (out or ""):
                    self.log_msg(f" [{s[-4:]}] ✅ {filename} Instalado OK.", "success")
                else:
                    self.log_msg(f" [{s[-4:]}] ❌ Error instalando: {err or out}", "error")
                    
            # Use batch of 2 to not overwhelm ADB bridge
            with ThreadPoolExecutor(max_workers=2) as executor:
                executor.map(install_on_dev, self.engine.active_devices)
                
            self.log_msg(f" Instalación masiva de {filename} Terminada.", "success")
            
            if hasattr(self, 'install_apk_btn'):
                self.after(0, lambda: self.install_apk_btn.configure(text=" 📦 Instalar APK Externa a Todos", state="normal", fg_color="#6366F1"))
                
        threading.Thread(target=_installer, daemon=True).start()

    def build_control_tab(self):
        self.tab_ctrl.grid_columnconfigure(0, weight=1)
        self.tab_ctrl.grid_columnconfigure(1, weight=1)
        self.tab_ctrl.grid_rowconfigure(1, weight=1)

        # left controls
        frame = ctk.CTkScrollableFrame(self.tab_ctrl)
        frame.grid(row=1, column=0, pady=10, padx=10, sticky="nsew")
        
        ctk.CTkLabel(frame, text="🔒 Configuración de Red (Proxys)", font=("Arial", 16, "bold")).pack(pady=5)
        
        prx_frame = ctk.CTkFrame(frame, fg_color="transparent")
        prx_frame.pack(fill="x", pady=(10, 5))
        
        self.no_proxy_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(prx_frame, text="🛡️ Modo Sin Proxy (Internet del PC)", variable=self.no_proxy_var, font=("Arial", 12, "bold"), text_color="#10B981").pack(side="left", padx=10)
        
        self.bot_only_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(prx_frame, text="📶 Modo Solo Bot (WiFi Celular)", variable=self.bot_only_var, font=("Arial", 12, "bold"), text_color="#FCD34D").pack(side="left", padx=5)
        
        self.test_btn = ctk.CTkButton(prx_frame, text="🧪 Probador", width=80, fg_color="#F59E0B", command=self.test_proxies)
        self.test_btn.pack(side="right", padx=10)

        self.proxy_textbox = ctk.CTkTextbox(frame, height=120)
        self.proxy_textbox.pack(pady=5, padx=10, fill="x")
        self.proxy_textbox.insert("1.0", "# IP:PORT:USER:PASS o similar\n")
        
        ctk.CTkLabel(frame, text="🎮 Controles Maestros", font=("Arial", 16, "bold")).pack(pady=(20, 5))
        
        scan_frame = ctk.CTkFrame(frame, fg_color="transparent")
        scan_frame.pack(fill="x", pady=5)
        
        self.scan_btn = ctk.CTkButton(scan_frame, text="🔍 1. Escanear Dispositivos", command=self.scan_devices, font=("Arial", 14, "bold"), height=35)
        self.scan_btn.pack(side="left", padx=10, expand=True, fill="x")
        
        self.reset_adb_btn = ctk.CTkButton(scan_frame, text="🔌 Reset USB", command=self.restart_adb_server, fg_color="#EF4444")
        self.reset_adb_btn.pack(side="right", padx=(0, 10), expand=True, fill="x")
        
        install_frame = ctk.CTkFrame(frame, fg_color="transparent")
        install_frame.pack(fill="x", pady=10)
        self.install_btn = ctk.CTkButton(install_frame, text="⚙️ 2. Instalar Motor Red", command=self.install_gnirehtet, fg_color="green", font=("Arial", 12, "bold"), height=35)
        self.install_btn.pack(side="left", padx=10, expand=True, fill="x")
        self.uninstall_btn = ctk.CTkButton(install_frame, text="🗑️ Quitar Motor", command=self.uninstall_gnirehtet, fg_color="#991B1B", hover_color="#7F1D1D", font=("Arial", 12, "bold"), height=35)
        self.uninstall_btn.pack(side="right", padx=(0,10), expand=True, fill="x")

        self.assign_btn = ctk.CTkButton(frame, text="🎯 ASIGNAR PROXYS A DISPOSITIVOS", command=self.assign_proxies, fg_color="#F59E0B", font=("Arial", 14, "bold"), height=35)
        self.assign_btn.pack(pady=10, padx=10, fill="x")

        self.start_btn = ctk.CTkButton(frame, text="▶️ 3. CREAR TÚNEL CENTRAL (INTERNET)", command=self.attempt_start, height=45, font=("Arial", 15, "bold"))
        self.start_btn.pack(pady=20, padx=10, fill="x")
        
        self.repair_btn = ctk.CTkButton(frame, text="🔧 REPARAR CAÍDOS", command=self.repair_failed_devices, state="disabled", fg_color="#F59E0B", font=("Arial", 12, "bold"))
        self.repair_btn.pack(pady=5, padx=10, fill="x")
        
        self.clean_btn = ctk.CTkButton(frame, text="💀 PANIC: CERRAR TODO", command=self.panic_clean, fg_color="darkred")
        self.clean_btn.pack(pady=10, padx=10, fill="x")

        # Right Cards
        self._right_container = ctk.CTkFrame(self.tab_ctrl, fg_color="transparent")
        self._right_container.grid(row=1, column=1, pady=10, padx=10, sticky="nsew")

        btn = ctk.CTkButton(self._right_container, text="📊 Obtener Diagnóstico Global", height=30, command=self.run_global_report, fg_color="#059669")
        btn.pack(fill="x", pady=(0, 5))

        sel_frame = ctk.CTkFrame(self._right_container, fg_color="#1A1A2E", corner_radius=8)
        sel_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkButton(sel_frame, text="☑ Todos", width=90, height=28, command=self.select_all_devices, fg_color="#10B981").pack(side="left", padx=5, pady=5)
        ctk.CTkButton(sel_frame, text="☐ Ninguno", width=90, height=28, command=self.deselect_all_devices, fg_color="#6B7280").pack(side="left", padx=5, pady=5)
        self.selection_count_lbl = ctk.CTkLabel(sel_frame, text="0 de 0 seleccionados", font=("Arial", 12, "bold"), text_color="#60A5FA")
        self.selection_count_lbl.pack(side="right", padx=10, pady=5)

        self.dev_frame = ctk.CTkScrollableFrame(self._right_container, label_text="📱 Tarjetas de Dispositivos")
        self.dev_frame.pack(fill="both", expand=True)
        self.device_widgets = []
        


    def build_traffic_tab(self):
        # MODO MAESTRO
        master_frame = ctk.CTkFrame(self.tab_traf, fg_color="#1E293B", corner_radius=8)
        master_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        ctk.CTkLabel(master_frame, text="⚙️ MODO DE OPERACIÓN MAESTRO", font=("Arial", 14, "bold"), text_color="#F59E0B").pack(pady=5)
        
        rb_frame = ctk.CTkFrame(master_frame, fg_color="transparent")
        rb_frame.pack(pady=5)
        
        ctk.CTkRadioButton(rb_frame, text="🟢 SOLO SPOTIFY", variable=self.master_mode, value="spotify", font=("Arial", 12, "bold"), text_color="#10B981").pack(side="left", padx=10)
        ctk.CTkRadioButton(rb_frame, text="🟣 SOLO YT MUSIC", variable=self.master_mode, value="yt_music", font=("Arial", 12, "bold"), text_color="#C026D3").pack(side="left", padx=10)
        ctk.CTkRadioButton(rb_frame, text="🔴 SOLO YT VIDEO", variable=self.master_mode, value="yt_video", font=("Arial", 12, "bold"), text_color="#EF4444").pack(side="left", padx=10)
        ctk.CTkRadioButton(rb_frame, text="🟡 MIXTO (Rotativo)", variable=self.master_mode, value="mixed", font=("Arial", 12, "bold"), text_color="#F59E0B").pack(side="left", padx=10)

        # Cajas de URLs
        url_frame = ctk.CTkFrame(self.tab_traf, fg_color="transparent")
        url_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        # Caja 1: Spotify
        spot_frame = ctk.CTkFrame(url_frame, fg_color="#064E3B", corner_radius=8) # Dark green
        spot_frame.pack(side="left", fill="both", expand=True, padx=(0, 2))
        self.use_spotify = ctk.BooleanVar(value=True)
        self.spotify_explore_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(spot_frame, text="🟢 Spotify (Listas):", font=("Arial", 11, "bold"), text_color="white", variable=self.use_spotify).pack(anchor="w", padx=10, pady=(2, 0))
        self.playlist_textbox = ctk.CTkTextbox(spot_frame, height=65)
        self.playlist_textbox.pack(padx=5, pady=0, fill="x")
        
        ctk.CTkLabel(spot_frame, text="🎸 Canciones Sueltas:", font=("Arial", 11, "bold"), text_color="white").pack(anchor="w", padx=10, pady=(2, 0))
        self.tracks_textbox = ctk.CTkTextbox(spot_frame, height=65)
        self.tracks_textbox.pack(padx=5, pady=0, fill="x")
        
        spot_btn_frame = ctk.CTkFrame(spot_frame, fg_color="transparent")
        spot_btn_frame.pack(fill="x", padx=5, pady=(0, 5))
        ctk.CTkButton(spot_btn_frame, text="💾", width=30, height=24, fg_color="#F59E0B", command=self.save_config).pack(side="left", padx=(0, 5))
        ctk.CTkButton(spot_btn_frame, text="🗑️", width=30, height=24, fg_color="#4B5563", command=lambda: self.playlist_textbox.delete("1.0", "end")).pack(side="left")
        
        # Modo Spotify
        self.spotify_mode_var = ctk.StringVar(value="Normal")
        self.spotify_mode_menu = ctk.CTkOptionMenu(spot_btn_frame, values=["Normal", "Explorar Artistas", "Clonar Copia"], variable=self.spotify_mode_var, width=130, height=24, font=("Arial", 11), fg_color="#10B981", button_color="#059669", command=self.on_spotify_mode_change)
        self.spotify_mode_menu.pack(side="right", padx=(5, 0))

        # Caja 2: YT Music
        ytm_frame = ctk.CTkFrame(url_frame, fg_color="#4A044E", corner_radius=8) # Dark purple
        ytm_frame.pack(side="left", fill="both", expand=True, padx=2)
        self.use_ytmusic = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(ytm_frame, text="🟣 YT Music (Listas):", font=("Arial", 11, "bold"), text_color="white", variable=self.use_ytmusic).pack(anchor="w", padx=10, pady=(5, 0))
        self.ytmusic_textbox = ctk.CTkTextbox(ytm_frame, height=160)
        self.ytmusic_textbox.pack(padx=5, pady=2, fill="x")
        
        ytm_btn_frame = ctk.CTkFrame(ytm_frame, fg_color="transparent")
        ytm_btn_frame.pack(fill="x", padx=5, pady=(0, 5))
        ctk.CTkButton(ytm_btn_frame, text="💾", width=30, height=24, fg_color="#F59E0B", command=self.save_config).pack(side="left", padx=(0, 5))
        ctk.CTkButton(ytm_btn_frame, text="🗑️", width=30, height=24, fg_color="#4B5563", command=lambda: self.ytmusic_textbox.delete("1.0", "end")).pack(side="left")

        # Caja 3: YT Video
        yt_frame = ctk.CTkFrame(url_frame, fg_color="#7F1D1D", corner_radius=8) # Dark red
        yt_frame.pack(side="right", fill="both", expand=True, padx=(2, 0))
        self.use_ytvideo = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(yt_frame, text="🔴 YT Video (Links):", font=("Arial", 11, "bold"), text_color="white", variable=self.use_ytvideo).pack(anchor="w", padx=10, pady=(5, 0))
        self.youtube_textbox = ctk.CTkTextbox(yt_frame, height=160)
        self.youtube_textbox.pack(padx=5, pady=2, fill="x")
        
        yt_btn_frame = ctk.CTkFrame(yt_frame, fg_color="transparent")
        yt_btn_frame.pack(fill="x", padx=5, pady=(0, 5))
        ctk.CTkButton(yt_btn_frame, text="💾", width=30, height=24, fg_color="#F59E0B", command=self.save_config).pack(side="left", padx=(0, 5))
        ctk.CTkButton(yt_btn_frame, text="🗑️", width=30, height=24, fg_color="#4B5563", command=lambda: self.youtube_textbox.delete("1.0", "end")).pack(side="left")
        
        self.youtube_web_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(yt_frame, text="🌐 En Chrome", variable=self.youtube_web_var, text_color="white", font=("Arial", 10, "bold"), checkbox_height=18, checkbox_width=18).pack(pady=(0, 5), padx=5, anchor="w")

        # Controles y Anti-Bots
        ctrl_frame = ctk.CTkFrame(self.tab_traf, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        # Interruptor de rotación automática
        self.media_rot_switch = ctk.CTkSwitch(ctrl_frame, text="▶️ Inyección Automática", variable=self.media_rotation_active, progress_color="#10B981")
        self.media_rot_switch.pack(side="left", padx=10)
        
        ctk.CTkLabel(ctrl_frame, text="Rotar cada (Minutos):").pack(side="left", padx=5)
        self.pl_interval_entry = ctk.CTkEntry(ctrl_frame, textvariable=self.playlist_interval, width=50, justify="center")
        self.pl_interval_entry.pack(side="left", padx=5)
        
        ctk.CTkCheckBox(ctrl_frame, text="💧 Goteo Humano", variable=self.youtube_drip_var).pack(side="left", padx=(15, 5))
        
        # Inyectores manuales
        self.btn_manual_spotify = ctk.CTkButton(ctrl_frame, text="Spotify", width=55, fg_color="#10B981", command=self.inject_manual_playlist)
        self.btn_manual_spotify.pack(side="right", padx=2)
        
        self.btn_manual_ytmusic = ctk.CTkButton(ctrl_frame, text="YT Music", width=65, fg_color="#C026D3", command=self.inject_manual_ytmusic)
        self.btn_manual_ytmusic.pack(side="right", padx=2)
        
        self.btn_manual_youtube = ctk.CTkButton(ctrl_frame, text="YT Video", width=65, fg_color="#EF4444", command=self.inject_manual_youtube)
        self.btn_manual_youtube.pack(side="right", padx=2)
        
        self.btn_manual_mixed = ctk.CTkButton(ctrl_frame, text="Mixto", width=55, fg_color="#F59E0B", command=self.inject_manual_mixed)
        self.btn_manual_mixed.pack(side="right", padx=2)
        
        # Display Dashboard en vivo
        self.live_status_var = ctk.StringVar(value="Estado: ⏸️ ESPERANDO...")
        dashboard_frame = ctk.CTkFrame(self.tab_traf, fg_color="#0F172A", corner_radius=8, border_width=1, border_color="#FCD34D")
        dashboard_frame.pack(fill="x", padx=10, pady=(10, 0))
        self.live_status_lbl = ctk.CTkLabel(dashboard_frame, textvariable=self.live_status_var, font=("Courier New", 14, "bold"), text_color="#FCD34D")
        self.live_status_lbl.pack(pady=8)
        
        # Inicializar el estado de la UI
        self.after(100, self.update_ui_state)

        # Shield
        shield_frame = ctk.CTkFrame(self.tab_traf, fg_color="#1E1E1E", border_width=1, border_color="#F59E0B", corner_radius=8)
        shield_frame.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(shield_frame, text="🛡️ Escudo Anti-Bots", font=("Arial", 12, "bold"), text_color="#60A5FA").pack(side="left", padx=10, pady=5)
        
        ctk.CTkCheckBox(shield_frame, text="Auto-Reinicio", variable=self.watchdog_enabled, text_color="#94A3B8").pack(side="left", padx=(10, 5), pady=5)
        ctk.CTkCheckBox(shield_frame, text="Toques Fantasma", variable=self.ghost_enabled, text_color="#94A3B8").pack(side="left", padx=5, pady=5)
        
        btn_bot = ctk.CTkCheckBox(shield_frame, text="Saltos Impacientes", variable=self.bot_enabled, text_color="#10B981")
        btn_bot.pack(side="left", padx=5, pady=5)
        self.bind_tooltip(btn_bot, "Simula ser humano: escucha 5-7 canciones completas, luego salta impacientemente la 8va al minuto 1.")
        
        ctk.CTkButton(shield_frame, text="🧹 Limpiar Caché", fg_color="#B91C1C", width=110, command=self.clear_yt_music_cache).pack(side="right", padx=10, pady=5)

        # Toolbar with sorting buttons
        toolbar = ctk.CTkFrame(self.tab_traf, fg_color="#1A1A2E", corner_radius=8)
        toolbar.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(toolbar, text="Ordenar:", font=("Arial", 11), text_color="#94A3B8").pack(side="left", padx=(10, 5), pady=5)
        ctk.CTkButton(toolbar, text="🔤 Por Serial", width=120, height=28, command=lambda: self.sort_traffic("serial"), fg_color="#F59E0B").pack(side="left", padx=5, pady=5)
        ctk.CTkButton(toolbar, text="🟢 Por Conexión", width=130, height=28, command=lambda: self.sort_traffic("connection"), fg_color="#10B981").pack(side="left", padx=5, pady=5)
        self.traf_sort_lbl = ctk.CTkLabel(toolbar, text="Sin ordenar", font=("Arial", 10), text_color="#64748B")
        self.traf_sort_lbl.pack(side="right", padx=10, pady=5)

        # Contenedor inferior dividido
        split_frame = ctk.CTkFrame(self.tab_traf, fg_color="transparent")
        split_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.traf_frame = ctk.CTkScrollableFrame(split_frame)
        self.traf_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        title = ctk.CTkLabel(self.traf_frame, text="Semáforo de Consumo en Tiempo Real", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        log_container = ctk.CTkFrame(split_frame, fg_color="#111827", corner_radius=8)
        log_container.pack(side="right", fill="both", expand=True, padx=(5, 0))
        ctk.CTkLabel(log_container, text="Log de Operaciones", font=("Arial", 16, "bold"), text_color="#34D399").pack(pady=10)
        self.log_frame_bottom = ctk.CTkTextbox(log_container, font=("Consolas", 11), text_color="#10B981", fg_color="transparent")
        self.log_frame_bottom.pack(fill="both", expand=True, padx=5, pady=5)
        self.traf_widgets = {}  # serial -> label widget
        self.traf_data = {}  # serial -> {is_active, rx, tx, ip, text, color}
        self.traf_sort_mode = None  # None, "serial", "connection"


    def update_ui_state(self, *args):
        if not hasattr(self, 'btn_manual_spotify'): return
        mode = self.master_mode.get()
        
        # Reset all to disabled by default
        self.btn_manual_spotify.configure(state="disabled", fg_color="#374151")
        self.btn_manual_ytmusic.configure(state="disabled", fg_color="#374151")
        self.btn_manual_youtube.configure(state="disabled", fg_color="#374151")
        
        if mode == "spotify":
            self.btn_manual_spotify.configure(state="normal", fg_color="#10B981")
        elif mode == "yt_music":
            self.btn_manual_ytmusic.configure(state="normal", fg_color="#C026D3")
        elif mode == "yt_video":
            self.btn_manual_youtube.configure(state="normal", fg_color="#EF4444")
        else: # mixed
            self.btn_manual_spotify.configure(state="normal", fg_color="#10B981")
            self.btn_manual_ytmusic.configure(state="normal", fg_color="#C026D3")
            self.btn_manual_youtube.configure(state="normal", fg_color="#EF4444")
            
        # Obsolete network rotation state
        if hasattr(self, 'network_rotation_enabled'):
            state = "normal" if self.network_rotation_enabled.get() else "disabled"
            color = "#FFFFFF" if self.network_rotation_enabled.get() else "#6B7280" # gris
            
            self.batch_entry.configure(state=state)
            self.mins_entry.configure(state=state)

    def log_msg(self, msg, type="info"):
        def _update():
            self.log_frame.configure(state="normal")
            sym = "🟢" if type == "info" else "✅"
            if type == "warn": sym = "⚠️"
            full_msg = f"{sym} {msg}\n"
            self.log_frame.insert("end", full_msg)
            self.log_frame.see("end")
            self.log_frame.configure(state="disabled")
            if hasattr(self, 'log_frame_bottom'):
                try:
                    self.log_frame_bottom.configure(state="normal")
                    self.log_frame_bottom.insert("end", full_msg)
                    self.log_frame_bottom.see("end")
                    self.log_frame_bottom.configure(state="disabled")
                except:
                    pass
        if hasattr(self, 'after'):
            self.after(0, _update)
        else:
            _update()

    def restart_adb_server(self):
        def _task():
            self.log_msg("⚠️ Matando motor USB (ADB)... (Desconectará otras apps brevemente)", "warn")
            import subprocess
            self.adb.run_command(["kill-server"])
            subprocess.run(["taskkill", "/F", "/IM", "adb.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            self.log_msg("🚀 Reviviendo motor USB...", "info")
            self.adb.run_command(["start-server"])
            time.sleep(2)
            self.log_msg("✅ Motor reiniciado. Escaneando celulares...", "info")
            self.scan_devices()
        threading.Thread(target=_task, daemon=True).start()

    def scan_devices(self):
        self.scan_btn.configure(state="disabled", text="🔍 Escaneando... (Espera)")
        ScanProgressWindow(self, self.adb, self._finish_scan)

    def load_config(self):
        try:
            with open("config.json", "r") as f:
                import json
                data = json.load(f)
                
                if "proxies" in data and hasattr(self, 'proxy_textbox'):
                    self.proxy_textbox.delete("1.0", "end")
                    self.proxy_textbox.insert("1.0", data["proxies"].strip() + "\n")
                
                if hasattr(self, 'ig_textbox') and "ig_playlists" in data:
                    self.ig_textbox.delete("1.0", "end")
                    self.ig_textbox.insert("1.0", data["ig_playlists"].strip() + "\n")
                    
                if hasattr(self, 'kick_textbox') and "kick_playlists" in data:
                    self.kick_textbox.delete("1.0", "end")
                    self.kick_textbox.insert("1.0", data["kick_playlists"].strip() + "\n")
                    
                if hasattr(self, 'kick_chat_textbox') and "kick_chat" in data:
                    self.kick_chat_textbox.delete("1.0", "end")
                    self.kick_chat_textbox.insert("1.0", data["kick_chat"].strip() + "\n")
                    
                if hasattr(self, 'no_proxy_var'):
                    self.no_proxy_var.set(data.get("no_proxy", False))
                if hasattr(self, 'bot_only_var'):
                    self.bot_only_var.set(data.get("bot_only", False))
                if hasattr(self, 'kick_interact'):
                    self.kick_interact.set(data.get("kick_interact", False))
                if hasattr(self, 'acc_slow_mode_var'):
                    self.acc_slow_mode_var.set(data.get("acc_slow_mode", False))
        except:
            pass


    def save_config(self):
        try:
            data = {}
            
            # Proxies
            if hasattr(self, 'proxy_textbox'):
                data["proxies"] = self.proxy_textbox.get("1.0", "end").strip()
                
            # Cajas de Redes Sociales
            if hasattr(self, 'ig_textbox'):
                data["ig_playlists"] = self.ig_textbox.get("1.0", "end").strip()
            if hasattr(self, 'kick_textbox'):
                data["kick_playlists"] = self.kick_textbox.get("1.0", "end").strip()
            if hasattr(self, 'kick_chat_textbox'):
                data["kick_chat"] = self.kick_chat_textbox.get("1.0", "end").strip()
                
            # Opciones
            if hasattr(self, 'no_proxy_var'):
                data["no_proxy"] = self.no_proxy_var.get()
            if hasattr(self, 'bot_only_var'):
                data["bot_only"] = self.bot_only_var.get()
            if hasattr(self, 'kick_interact'):
                data["kick_interact"] = self.kick_interact.get()
            if hasattr(self, 'acc_slow_mode_var'):
                data["acc_slow_mode"] = self.acc_slow_mode_var.get()
                
            import json
            with open("config.json", "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            self.log_msg(f" Error guardando config: {e}", "error")

    def show_inventory(self):
        InventoryWindow(self)

    def _finish_scan(self, devices):
        self.scanned_devices = devices
        pkg_missing = len([d for d in devices if not d.get('pkg_ok')])
        msg = f"Escaner completado: {len(devices)} conectados."
        if pkg_missing > 0:
            msg += f" ⚠️ {pkg_missing} requieren instalación de driver."
        else:
            msg += " ✅ Todos con driver OK."
        
        self.log_msg(msg)
        for w in self.device_widgets:
            w.destroy()
        self.device_widgets = []
        self.device_selections = {}
        for dev in devices:
            var = ctk.BooleanVar(value=True)
            var.trace_add("write", lambda *_: self.update_selection_count())
            self.device_selections[dev['serial']] = var
            self.create_device_card(dev)
        self.update_selection_count()
        self.update_account_creator_devices()
        self.scan_btn.configure(state="normal", text="🔍 1. Escanear Dispositivos")

    def create_device_card(self, dev):
        card = ctk.CTkFrame(self.dev_frame, fg_color="#1E1E1E", corner_radius=10, border_width=1, border_color="#333333")
        card.pack(fill="x", pady=4, padx=4)
        conn_type = "📶 WiFi" if dev['is_wifi'] else "🔌 USB"
        
        # Checkbox for device selection
        check_fr = ctk.CTkFrame(card, fg_color="transparent", width=40)
        check_fr.pack(side="left", padx=(10, 0), pady=10)
        sel_var = self.device_selections.get(dev['serial'])
        if sel_var:
            cb = ctk.CTkCheckBox(check_fr, text="", variable=sel_var, width=24, checkbox_width=22, checkbox_height=22)
            cb.pack()
        
        left_fr = ctk.CTkFrame(card, fg_color="transparent")
        left_fr.pack(side="left", padx=5, pady=4, fill="y")
        model_name = dev.get('model', 'Phone')
        title = ctk.CTkLabel(left_fr, text=f"{model_name}", font=("Arial", 14, "bold"))
        title.pack(anchor="w")
        # Driver status on left
        pkg_ok = dev.get('pkg_ok', False)
        status_color = "#10B981" if pkg_ok else "#EF4444"
        status_txt = "✅ Driver OK" if pkg_ok else "❌ Sin Driver"
        ctk.CTkLabel(left_fr, text=status_txt, text_color=status_color, font=("Arial", 10, "bold")).pack(anchor="w")
        ctk.CTkLabel(left_fr, text=f"{conn_type}", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        ctk.CTkLabel(left_fr, text=f"ID: {dev['serial']}", text_color="#94A3B8", font=("Arial", 9)).pack(anchor="w")
        
        mid_fr = ctk.CTkFrame(card, fg_color="transparent")
        mid_fr.pack(side="left", padx=10, pady=4, fill="y", expand=True)
        # Timer
        timer_lbl = ctk.CTkLabel(mid_fr, text="⏳ Esperando...", font=("Arial", 11), text_color="#94A3B8")
        timer_lbl.pack(anchor="w")
        # IP Display
        ctk.CTkLabel(mid_fr, text="IP EXTERNA:", font=("Arial", 10), text_color="gray").pack(anchor="w")
        ip_val_lbl = ctk.CTkLabel(mid_fr, text="Detectando...", text_color="#FCD34D", font=("Arial", 15, "bold"))
        ip_val_lbl.pack(anchor="w")
        
        # Traffic on right
        right_info = ctk.CTkFrame(card, fg_color="transparent")
        right_info.pack(side="right", padx=8)
        traffic_lbl = ctk.CTkLabel(right_info, text="MB: 0.0↓ 0.0↑", font=("Courier New", 12))
        traffic_lbl.pack()
        # Health status indicator
        health_lbl = ctk.CTkLabel(right_info, text="⭕ Sin estado", font=("Arial", 10), text_color="#64748B")
        health_lbl.pack(pady=(5, 0))

        # Interaction buttons row
        actions_fr = ctk.CTkFrame(right_info, fg_color="transparent")
        actions_fr.pack(pady=(5, 0))
        serial = dev['serial']
        ctk.CTkButton(actions_fr, text="👁️", width=36, height=26, fg_color="#F59E0B",
                      command=lambda s=serial: self.launch_scrcpy(s),
                      font=("Arial", 13)).pack(side="left", padx=2)
        focus_btn = ctk.CTkButton(actions_fr, text="🎯", width=36, height=26, fg_color="#F59E0B",
                      command=lambda s=serial: self.toggle_focus(s),
                      font=("Arial", 13))
        focus_btn.pack(side="left", padx=2)
        ctk.CTkButton(actions_fr, text="📋", width=36, height=26, fg_color="#059669",
                      command=lambda s=serial: self.paste_to_device(s),
                      font=("Arial", 13)).pack(side="left", padx=2)

        self.device_ui_map[dev['serial']] = {
            "card": card,
            "timer": timer_lbl,
            "ip": ip_val_lbl,
            "traffic": traffic_lbl,
            "health": health_lbl,
            "focus_btn": focus_btn
        }
        self.device_widgets.append(card)

    def select_all_devices(self):
        for var in self.device_selections.values():
            var.set(True)

    def deselect_all_devices(self):
        for var in self.device_selections.values():
            var.set(False)

    def update_selection_count(self):
        total = len(self.device_selections)
        selected = sum(1 for v in self.device_selections.values() if v.get())
        if hasattr(self, 'selection_count_lbl') and self.selection_count_lbl.winfo_exists():
            self.selection_count_lbl.configure(text=f"{selected} de {total} seleccionados")

    def get_selected_devices(self):
        """Returns only the scanned devices whose checkbox is checked."""
        return [d for d in self.scanned_devices if self.device_selections.get(d['serial'], ctk.BooleanVar(value=False)).get()]

    def launch_scrcpy(self, serial):
        """Launch scrcpy to mirror device screen."""
        base = os.path.dirname(os.path.abspath(__file__))
        scrcpy_exe = os.path.join(base, "scrcpy", "scrcpy.exe")
        if not os.path.exists(scrcpy_exe):
            messagebox.showerror("scrcpy no encontrado",
                "scrcpy no está instalado.\n\nCierra la app y ejecuta START_APP.bat para que se descargue automáticamente.")
            return
        try:
            subprocess.Popen([scrcpy_exe, "-s", serial, "--window-title", f"📱 {serial}", "--no-audio"],
                             cwd=os.path.join(base, "scrcpy"))
            self.log_msg(f"👁️ Pantalla abierta: {serial}")
        except Exception as e:
            self.log_msg(f"❌ Error al abrir pantalla: {e}", "error")

    def toggle_focus(self, serial):
        """Give full bandwidth to one device by pausing all others."""
        if not self.engine.running:
            messagebox.showinfo("Info", "El túnel debe estar activo para usar Focus.")
            return

        ui = self.device_ui_map.get(serial, {})
        focus_btn = ui.get("focus_btn")

        # Check if already in focus mode for this device
        if hasattr(self, '_focus_serial') and self._focus_serial == serial:
            # Restore all paused devices
            self.log_msg(f"↩️ Restaurando todos los dispositivos...")
            for paused_serial in self._focus_paused:
                self.runner.start(paused_serial)
            self._focus_serial = None
            self._focus_paused = []
            if focus_btn:
                focus_btn.configure(text="🎯", fg_color="#F59E0B")
            self.log_msg(f"✅ Todos los dispositivos restaurados.")
            return

        # Enter focus mode: pause gnirehtet on all OTHER active devices
        active_serials = [d['serial'] for d in self.engine.active_devices]
        if serial not in active_serials:
            messagebox.showinfo("Info", f"El dispositivo {serial[-4:]} no está en el lote activo.")
            return

        others = [s for s in active_serials if s != serial]
        if not others:
            messagebox.showinfo("Info", "Solo hay 1 dispositivo activo, ya tiene todo el tráfico.")
            return

        self._focus_serial = serial
        self._focus_paused = others
        self.log_msg(f"🎯 FOCUS → {serial[-4:]} | Pausando {len(others)} dispositivo(s)...", "warn")

        def _do_focus():
            for other in others:
                self.runner.stop(other)
            self.after(0, lambda: self.log_msg(f"🎯 {serial[-4:]} tiene todo el ancho de banda. Clic 🎯 de nuevo para restaurar."))

        threading.Thread(target=_do_focus, daemon=True).start()
        if focus_btn:
            focus_btn.configure(text="↩️", fg_color="#EF4444")

    def paste_to_device(self, serial):
        """Open dialog to paste text to device via ADB."""
        dialog = ctk.CTkInputDialog(text=f"Texto a pegar en {serial[-8:]}:", title="📋 Pegar en Dispositivo")
        text = dialog.get_input()
        if text and text.strip():
            # Escape special characters for ADB shell input
            safe_text = text.replace("\\", "\\\\").replace("\"", "\\\"").replace("'", "\\'")
            safe_text = safe_text.replace(" ", "%s").replace("&", "\\&").replace(";", "\\;")
            safe_text = safe_text.replace("(", "\\(").replace(")", "\\)").replace("|", "\\|")

            def _paste():
                # Method 1: Try clipboard broadcast (needs Clipper or similar)
                self.adb.run_command(["shell", "input", "text", safe_text], serial)
                self.after(0, lambda: self.log_msg(f"📋 Texto enviado a {serial[-4:]}: \"{text[:30]}...\"" if len(text) > 30 else f"📋 Texto enviado a {serial[-4:]}: \"{text}\""))

            threading.Thread(target=_paste, daemon=True).start()

    def run_global_report(self):
        ReporteGlobalWindow(self, self.adb, self.engine)

    def test_proxies(self):
        raw_proxies = self.proxy_textbox.get("1.0", "end").strip().split('\n')
        proxies = [from_engine for from_engine in [p.strip() for p in raw_proxies if p.strip() and not p.startswith("#")] if from_engine]
        from rotation_engine import format_proxy
        formatted = [format_proxy(p) for p in proxies if format_proxy(p)]
        if not formatted:
            messagebox.showwarning("Vacío", "Pega proxies para probarlos primero.")
            return

        def _on_test_finish(alive_list):
            self.proxy_textbox.delete("1.0", "end")
            self.proxy_textbox.insert("end", "# Proxies Testeados (Limpios)\n")
            for p in alive_list:
                self.proxy_textbox.insert("end", p + "\n")
            self.log_msg(f"Test finalizado. {len(alive_list)} proxies guardados y limpios.")
            self.save_config()

        ProxyTesterWindow(self, formatted, _on_test_finish)

    def uninstall_gnirehtet(self):
        selected = self.get_selected_devices()
        if not selected:
            messagebox.showerror("Error", "Selecciona al menos un dispositivo para desinstalar Gnirehtet.")
            return
        if messagebox.askyesno("Confirmar", f"¿Desinstalar Motor de Red (Gnirehtet) en {len(selected)} dispositivos?\nEsto permitirá que usen su Wi-Fi normal."):
            def _uninstall():
                self.log_msg(f"🗑️ Desinstalando Gnirehtet en {len(selected)} dispositivos...", "warn")
                for dev in selected:
                    s = dev['serial']
                    self.adb.run_command(["uninstall", "com.genymobile.gnirehtet"], s)
                self.after(0, lambda: self.log_msg("✅ Desinstalación completada.", "info"))
            import threading
            threading.Thread(target=_uninstall, daemon=True).start()

    def install_gnirehtet(self):
        devices = self.adb.list_devices()
        missing = [d for d in devices if not d.get('pkg_ok')]
        if not missing:
            messagebox.showinfo("Listo", "Todos los dispositivos ya tienen el driver instalado.")
            return
            
        def _installer():
            total = len(missing)
            self.log_msg(f"⚙️ Instalando driver en {total} dispositivos faltantes...", "warn")
            for i, dev in enumerate(missing):
                s = dev['serial']
                self.log_msg(f"📦 Instalando en {dev['model']} ({s})...")
                self.adb.install_apk(s, "gnirehtet.apk")
            self.log_msg(f"✅ ¡Instalación completada en {total} equipos!", "info")
            self.after(0, self.scan_devices) # Refresh to show green checks
            
        threading.Thread(target=_installer, daemon=True).start()

    def parse_inputs(self):
        return 9999, 999999.0

    def attempt_start(self):
        # Check that devices are selected
        selected = self.get_selected_devices()
        if not selected:
            messagebox.showerror("⛔ Sin Dispositivos", "No hay dispositivos seleccionados.\nEscanea y marca los que quieras usar.")
            return

        raw_proxies = self.proxy_textbox.get("1.0", "end").strip().split('\n')
        proxies = [p.strip() for p in raw_proxies if p.strip() and not p.startswith("#")]
        
        bot_only = getattr(self, 'bot_only_var', ctk.BooleanVar(value=False)).get()
        
        if not proxies:
            if self.no_proxy_var.get() or bot_only:
                self.save_config()
                self.start_farm([], tunnel_disabled=bot_only)
            else:
                self.no_proxy_strikes += 1
                if self.no_proxy_strikes >= 3:
                    if messagebox.askyesno("Info", f"Iniciando {len(selected)} dispositivos sin proxies. ¿Seguro?"): self.start_farm([])
                else:
                    messagebox.showerror("⛔ Faltan Proxies", "No ingresaste los Proxies.\n\n(O marca la casilla 'Modo Sin Proxy' o 'Modo Solo Bot')")
        else:
            self.save_config()
            self.start_farm(proxies, tunnel_disabled=bot_only)

    def assign_proxies(self):
        devices = self.adb.list_devices()
        if not devices:
            messagebox.showwarning("Vacío", "Escanea dispositivos primero para poder mapearlos.")
            return
        raw_proxies = self.proxy_textbox.get("1.0", "end").strip().split('\n')
        from rotation_engine import format_proxy
        proxies = [format_proxy(p) for p in raw_proxies if format_proxy(p)]
        if not proxies:
            messagebox.showwarning("Vacío", "Pega proxies en la lista primero.")
            return
            
        ProxyAssignmentWindow(self, devices, proxies)

    def start_farm(self, proxies, tunnel_disabled=False):
        devices = self.get_selected_devices()
        b_size, mins = self.parse_inputs()
        
        if b_size is None:
            return
            
        if not devices:
            messagebox.showerror("Falla Fatal", "No hay dispositivos seleccionados. Escanea y marca los que quieras usar.")
            self.log_msg("Intento de inicio abortado: 0 celulares seleccionados.", "warn")
            self.start_btn.configure(state="normal")
            return
            
        self.save_config()
        if tunnel_disabled:
            self.log_msg(f"📡 Iniciando en MODO SOLO BOT (Wifi Nativo) con {len(devices)} dispositivos...")
        else:
            self.log_msg(f"▶️ Iniciando Secuencia con {len(devices)} dispositivos seleccionados...")
        SetupProgressWindow(self, devices, proxies, b_size, mins, tunnel_disabled=tunnel_disabled)
        self.no_proxy_strikes = 0

    def repair_failed_devices(self):
        """Find devices with failed health and attempt reconnection."""
        failed = [s for s, h in self.device_health.items() if h.get("status") in ("dead", "warning")]
        if not failed:
            messagebox.showinfo("Sin Fallos", "No hay dispositivos caídos para reparar.")
            return

        self.repair_btn.configure(state="disabled", text="🔧 Reparando...")
        self.log_msg(f"🔧 Iniciando reparación de {len(failed)} dispositivo(s)...", "warn")

        def _repair_thread():
            results = {"fixed": 0, "still_broken": 0}
            for serial in failed:
                self.log_msg(f"  🔄 Reconectando {serial}...")
                success, reason = self.engine.reconnect_device(serial)
                if success:
                    results["fixed"] += 1
                    self.log_msg(f"  ✅ {serial}: {reason}")
                    self.device_health[serial] = {"status": "ok", "reason": reason}
                    self.last_ip_check[serial] = 0  # Force fresh IP check on next cycle
                else:
                    results["still_broken"] += 1
                    self.log_msg(f"  ❌ {serial}: {reason}", "error")
                    self.device_health[serial] = {"status": "dead", "reason": reason}

            # Summary
            summary = f"🔧 Resultado: {results['fixed']} reparados"
            if results["still_broken"] > 0:
                summary += f", {results['still_broken']} siguen fallando"
                self.log_msg(summary, "warn")
            else:
                self.log_msg(summary)

            self.after(0, lambda: self.repair_btn.configure(state="normal", text="🔧 REPARAR CAÍDOS"))

        threading.Thread(target=_repair_thread, daemon=True).start()

    def panic_clean(self):
        PanicProgressWindow(self, self.engine, self.runner, self.adb)


    def on_engine_update(self, event_type):
        if event_type == "COMPLETED":
            self.log_msg("✅ Ciclo completado. Granja terminada.")
            self.start_btn.configure(state="normal")
            self.pause_btn.configure(state="disabled")
            self.status_lbl.configure(text="Estado: COMPLETADO 🏁")

    def update_timer(self):
        if self.engine.running and not self.engine.paused:
            rem = int(self.engine.next_rotation_time - time.time())
            if rem > 0:
                m = rem // 60
                s = rem % 60
                self.status_lbl.configure(text=f"🔄 Lote {self.engine.current_batch_index + 1} ACTIVO | Cambio en: {m}m {s}s", text_color="lightgreen")
            else:
                self.status_lbl.configure(text="🔄 Cambiando de lote u Operando Stealth...", text_color="yellow")
        self.after(1000, self.update_timer)

    def update_traffic(self):
        if self.engine.running:
            devices = self.engine.all_devices.copy()
            active_serials = [d['serial'] for d in self.engine.active_devices]
            
            def _fetch():
                updates = {}
                threads = []
                
                def _fetch_one(serial, is_active):
                    rx_mb, tx_mb = 0.0, 0.0
                    external_ip = "---"
                    health = "offline"
                    health_reason = ""
                    if is_active:
                        # 1. Check tunnel interface (tun0 or vpn only, NOT rmnet)
                        has_tunnel = False
                        stdout, _, _ = self.adb.run_command(["shell", "cat", "/proc/net/dev"], serial)
                        for line in stdout.split('\n'):
                            if 'tun0:' in line or 'vpn' in line:
                                has_tunnel = True
                            # Traffic: collect from tun0, vpn, or rmnet
                            if 'tun0:' in line or 'vpn' in line or 'rmnet' in line:
                                try:
                                    p = line.split(':')[1].split()
                                    rx_mb += float(p[0]) / (1024 * 1024)
                                    tx_mb += float(p[8]) / (1024 * 1024)
                                except: pass
                        
                        if not has_tunnel:
                            health = "dead"
                            health_reason = "Sin túnel (tun0 ausente)"
                        
                        # 2. IP check from PC through local proxy port (every 60s)
                        last = self.last_ip_check.get(serial, 0)
                        if (time.time() - last) > 60:
                            port = self.engine.active_ports.get(serial)
                            if port:
                                try:
                                    import requests
                                    px = {"http": f"http://127.0.0.1:{port}", "https": f"http://127.0.0.1:{port}"}
                                    res = requests.get("https://api.ipify.org?format=json", proxies=px, timeout=6)
                                    ip = res.json().get("ip", "")
                                    if ip:
                                        external_ip = ip
                                        self.last_ip_check[serial] = time.time()
                                        health = "ok"
                                        health_reason = "Conexión OK"
                                        self.health_fail_count[serial] = 0
                                    else:
                                        raise Exception("empty")
                                except Exception:
                                    fails = self.health_fail_count.get(serial, 0) + 1
                                    self.health_fail_count[serial] = fails
                                    if fails >= 2:
                                        external_ip = "Sin respuesta"
                                        if has_tunnel:
                                            health = "warning"
                                            health_reason = "Proxy sin respuesta"
                                        else:
                                            health = "dead"
                                            health_reason = "Sin túnel ni internet"
                                    else:
                                        # First failure: keep previous state, don't alarm yet
                                        prev = self.device_health.get(serial, {})
                                        health = prev.get("status", "ok" if has_tunnel else "dead")
                                        health_reason = prev.get("reason", "Verificando...")
                                        ui = self.device_ui_map.get(serial)
                                        if ui: external_ip = ui['ip'].cget("text")
                                        self.last_ip_check[serial] = time.time()
                            else:
                                # No proxy port assigned: tunnel-only mode
                                if has_tunnel:
                                    health = "ok"
                                    health_reason = "Túnel directo (sin proxy)"
                                    external_ip = "Directo"
                                self.last_ip_check[serial] = time.time()
                        else:
                            # Between checks: keep current state
                            ui = self.device_ui_map.get(serial)
                            if ui: external_ip = ui['ip'].cget("text")
                            prev = self.device_health.get(serial, {})
                            if prev:
                                health = prev.get("status", "ok" if has_tunnel else "dead")
                                health_reason = prev.get("reason", "")
                            elif has_tunnel:
                                health = "ok"
                                health_reason = "Túnel activo"
                    
                    self.device_health[serial] = {"status": health, "reason": health_reason}
                    updates[serial] = (is_active, rx_mb, tx_mb, external_ip, health, health_reason)

                for dev in devices:
                    t = threading.Thread(target=_fetch_one, args=(dev['serial'], dev['serial'] in active_serials))
                    t.start()
                    threads.append(t)
                
                for t in threads: t.join()
                self.after(0, self._apply_traffic_updates, updates)
                
            threading.Thread(target=_fetch, daemon=True).start()
        self.after(5000, self.update_traffic)

    def _apply_traffic_updates(self, updates):
        now = time.time()
        rem_sec = max(0, int(self.engine.next_rotation_time - now))
        mins = rem_sec // 60
        secs = rem_sec % 60
        timer_text = f"⏳ Rotación: {mins:02d}:{secs:02d}"

        has_failed = False
        for serial, (is_active, rx, tx, ip, health, health_reason) in updates.items():
            ui = self.device_ui_map.get(serial)
            if ui:
                # 1. Update Timer & IP labels
                if is_active:
                    ui['timer'].configure(text=timer_text, text_color="#FCD34D")
                    if ip != "---":
                        ui['ip'].configure(text=ip)
                else:
                    ui['timer'].configure(text="🕒 En Espera...", text_color="#64748B")
                    ui['ip'].configure(text="Túnel Cerrado")
                
                # 2. Update Traffic info
                ui['traffic'].configure(text=f"MB: {rx:.1f}↓ {tx:.1f}↑")
                
                # 3. Health status display
                if is_active:
                    if health == "ok":
                        ui['health'].configure(text="🟢 OK", text_color="#10B981")
                        bg_color = "#064E3B"
                    elif health == "warning":
                        ui['health'].configure(text=f"🟡 {health_reason}", text_color="#F59E0B")
                        bg_color = "#78350F"
                        has_failed = True
                    elif health == "dead":
                        ui['health'].configure(text=f"🔴 {health_reason}", text_color="#EF4444")
                        bg_color = "#7F1D1D"
                        has_failed = True
                    else:
                        ui['health'].configure(text="⭕ Verificando...", text_color="#64748B")
                        bg_color = "#064E3B"
                else:
                    ui['health'].configure(text="💤 Inactivo", text_color="#475569")
                    bg_color = "#1E1E1E"
                
                ui['card'].configure(fg_color=bg_color)
            
            # 4. Global traffic list update
            if health == "ok":
                color = "#10B981"
                estado_txt = "🟢 OK"
            elif health == "warning":
                color = "#F59E0B"
                estado_txt = "🟡 LENTO"
            elif health == "dead" and is_active:
                color = "#EF4444"
                estado_txt = "🔴 CAÍDO"
            elif is_active:
                color = "#94A3B8"
                estado_txt = "⏳ CHECK"
            else:
                color = "gray"
                estado_txt = "🌙"
            text_disp = f"{estado_txt} │📱 {serial} │ {rx:.1f}MB↓ {tx:.1f}MB↑ │ IP: {ip}"

            pass # Removed traf_data block

        # Enable repair button if there are failures
        if has_failed:
            self.repair_btn.configure(state="normal")
        else:
            self.repair_btn.configure(state="disabled")



    def sort_traffic(self, mode):
        """Reorder traffic widgets by serial or connection status."""
        self.traf_sort_mode = mode
        if not self.traf_data:
            return

        serials = list(self.traf_data.keys())
        if mode == "serial":
            serials.sort()
            self.traf_sort_lbl.configure(text="Ordenado: A → Z (Serial)")
        elif mode == "connection":
            serials.sort(key=lambda s: (not self.traf_data[s]["is_active"], s))
            self.traf_sort_lbl.configure(text="Ordenado: Activos primero")

        for serial in serials:
            w = self.traf_widgets.get(serial)
            if w:
                w["frame"].pack_forget()
                w["frame"].pack(fill="x", pady=2)

    def watchdog_ghost_loop(self):
        import random
        import time
        while True:
            time.sleep(5) # Ciclo principal rápido
            try:
                if not hasattr(self, 'engine') or not self.engine.active_devices:
                    time.sleep(5)
                    continue
                    
                for dev in list(self.engine.active_devices):
                    serial = dev['serial']
                    
                    # Rotación secuencial: 10 segundos entre cada celular
                    time.sleep(10)
                    
                    if self.is_device_locked(serial):
                        continue
                    
                    # Watchdog: Every 10 mins (approx 10% chance per minute to check app focus)
                    if self.watchdog_enabled.get() and random.randint(1, 6) == 1:
                        out_tuple = self.adb.run_command(["shell", "dumpsys", "window", "windows", "|", "grep", "-E", "'mCurrentFocus|mFocusedApp'"], serial)
                        out = out_tuple[0] if isinstance(out_tuple, tuple) else out_tuple
                        if out:
                            # Valid audio/video packages
                            valid_pkgs = ["com.spotify.music", "com.google.android.youtube", "com.google.android.apps.youtube.music",
                                          "com.pandora.android", "fm.awa.app", "com.audiomack", "com.aspiro.tidal",
                                          "com.apple.android.music", "com.amazon.mp3", "com.kick.mobile"]

                            is_running = any(pkg in out for pkg in valid_pkgs)
                            is_kick = "com.kick.mobile" in out

                            if is_kick:
                                # Sistema de Auto-Curacion Kick
                                root = getattr(self, 'pull_and_parse', lambda x: None)(serial)
                                if root is not None:
                                    texts = [n.get("text", "").lower() for n in root.iter("node")]
                                    needs_rescue = False
                                    if "featured creators" in texts or "top live categories" in texts:
                                        needs_rescue = True
                                    elif "go back" in texts or "volver" in texts:
                                        self.log_msg(f"💥 [{serial[-4:]}] Error de red en Kick ('Go Back'/'Volver'). Rescatando...", "warn")
                                        self.find_and_click_by_text(serial, ["go back", "volver"])
                                        import time; time.sleep(2)
                                        needs_rescue = True
                                        
                                    if needs_rescue:
                                        self.log_msg(f"🚑 Protocolo de Rescate: {serial[-4:]} fuera del Live. Relanzando...", "error")
                                        if hasattr(self, 'kick_textbox'):
                                            urls = [u.strip() for u in self.kick_textbox.get("1.0", "end").strip().split("\n") if u.strip()]
                                            if urls:
                                                import threading
                                                def _rescue(s):
                                                    import random
                                                    streamer = random.choice(urls).rstrip('/').split('/')[-1]
                                                    self._kick_search_and_enter(s, streamer, is_slow=False)
                                                    self.interact_kick_stream(s)
                                                threading.Thread(target=_rescue, args=(serial,), daemon=True).start()
                                                continue # Skip standard restore

                            if not is_running:
                                self.log_msg(f"🛡️ Watchdog: App cerrada en {serial[-4:]}. Restaurando...", "warn")
                                # Trigger re-injection
                                if self.master_mode.get() == "spotify":
                                    playlists = [p.strip() for p in self.playlist_textbox.get("1.0", "end").strip().split('\n') if p.strip()]
                                    tracks = [t.strip() for t in getattr(self, 'tracks_textbox', type('obj', (object,), {'get': lambda *a: ''})()).get("1.0", "end").strip().split('\n') if t.strip()]
                                    if playlists: 
                                        self._inject_playlist_to_single(serial, random.choice(playlists))
                                    elif tracks:
                                        if hasattr(self, '_track_timers'): self._track_timers[serial] = __import__('time').time()
                                        self._inject_playlist_to_single(serial, random.choice(tracks))
                                elif self.master_mode.get() == "youtube":
                                    urls = [p.strip() for p in self.youtube_textbox.get("1.0", "end").strip().split('\n') if p.strip()]
                                    if urls: self._inject_youtube_to_single(serial, random.choice(urls))
                                else:
                                    # Modo mixto: Inyectar aleatoriamente una playlist de Spotify como fallback de seguridad
                                    playlists = [p.strip() for p in self.playlist_textbox.get("1.0", "end").strip().split('\n') if p.strip()]
                                    if playlists: self._inject_playlist_to_single(serial, random.choice(playlists))

                    # Ghost Touch Inteligente (Escaner Rápido de YouTube)
                    if self.ghost_enabled.get():
                        if not getattr(self, '_is_spotify_playing', lambda x: True)(serial):
                            self.log_msg(f" 👻 Escáner Anti-Pausa: Audio Pausado en {serial[-4:]}. Buscando cartel...", "warn")
                            
                            # 1. Intentar aceptar pop-up de YT Music ("¿Quieres seguir mirándolo?")
                            root = getattr(self, 'pull_and_parse', lambda x: None)(serial)
                            if root is not None:
                                texts = [n.get("text", "").lower() for n in root.iter("node")]
                                if any("mir" in t or "pausa" in t for t in texts):
                                    if getattr(self, 'find_and_click_by_text', lambda s, t: False)(serial, ["Sí", "Yes", "Si"]):
                                        self.log_msg(f" 👆 Popup de 'Seguir mirándolo' aceptado en {serial[-4:]}.", "success")
                                        time.sleep(1)

                            # 2. Tocar parte superior para cerrar anuncios (Opcional, si tap 360,300 pausa, mejor dar play primero)
                            self.adb.run_command(["shell", "input", "tap", "360", "200"], serial)
                            time.sleep(1)

                            # 3. Dar Play (85) y Adelantar (87) para forzar reactivación
                            self.adb.run_command(["shell", "input", "keyevent", "85"], serial) # Play
                            time.sleep(1)
                            self.adb.run_command(["shell", "input", "keyevent", "87"], serial) # Next (Adelantar)
                        
                        else:
                            # 4. Si YA está sonando bien (Play activo)
                            # Aleatoriamente adelantamos la cancion/video para saltar posibles anuncios o mantener el flujo
                            if random.randint(1, 10) == 1:
                                self.log_msg(f" ⏭️ Escáner Activo: Adelantando pista en {serial[-4:]} para fluidez...", "info")
                                self.adb.run_command(["shell", "input", "keyevent", "87"], serial) # Next
                                
                            # Ocasionalmente un ajuste humano (volumen invisible)
                            elif random.randint(1, 5) == 1:
                                for _ in range(15):
                                    self.adb.run_command(["shell", "input", "keyevent", "25"], serial)
                                time.sleep(0.5)
                                for _ in range(random.randint(2, 3)):
                                    self.adb.run_command(["shell", "input", "keyevent", "24"], serial)
            except Exception as e:
                pass


    def build_social_tab(self):
        self.tab_social.grid_columnconfigure(0, weight=1)
        
        main_frame = ctk.CTkScrollableFrame(self.tab_social, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # KICK (Now takes the whole tab)
        kick_frame = ctk.CTkFrame(main_frame, fg_color="#14532D", corner_radius=12)
        kick_frame.pack(fill="both", expand=True, pady=10)
        
        ctk.CTkLabel(kick_frame, text="🟢 Kick Automator", font=("Arial", 24, "bold"), text_color="#22C55E").pack(pady=20)
        
        # --- Bot en Cascada ---
        bot_frame = ctk.CTkFrame(kick_frame, fg_color="#1a1a2e", corner_radius=10)
        bot_frame.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(bot_frame, text="Bot de Comentarios en Cascada", font=("Arial", 14, "bold"), text_color="#9333EA").pack(anchor="w", padx=15, pady=(10,5))
        
        # Checkboxes for type of interaction
        type_row = ctk.CTkFrame(bot_frame, fg_color="transparent")
        type_row.pack(fill="x", padx=15, pady=(0, 5))
        self.kick_bot_type_comments = ctk.BooleanVar(value=True)
        self.kick_bot_type_emojis = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(type_row, text="Texto", variable=self.kick_bot_type_comments, font=("Arial", 12)).pack(side="left", padx=(0,10))
        ctk.CTkCheckBox(type_row, text="Emojis Verdes", variable=self.kick_bot_type_emojis, font=("Arial", 12)).pack(side="left")

        interval_row = ctk.CTkFrame(bot_frame, fg_color="transparent")
        interval_row.pack(fill="x", padx=15, pady=(0,5))
        ctk.CTkLabel(interval_row, text="Intervalo entre comentarios:", font=("Arial", 12), text_color="white").pack(side="left")
        self.kick_bot_interval = ctk.CTkOptionMenu(interval_row, values=["5 min", "7 min", "10 min", "15 min"], width=100)
        self.kick_bot_interval.pack(side="left", padx=10)
        self.kick_bot_interval.set("7 min")
        btn_row = ctk.CTkFrame(bot_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0,10))
        self.kick_bot_start_btn = ctk.CTkButton(btn_row, text="INICIAR BOT", fg_color="#16a34a", hover_color="#15803d", font=("Arial", 13, "bold"), command=self.start_cascade_bot)
        self.kick_bot_start_btn.pack(side="left", padx=(0,10))
        self.kick_bot_stop_btn = ctk.CTkButton(btn_row, text="DETENER BOT", fg_color="#dc2626", hover_color="#b91c1c", font=("Arial", 13, "bold"), command=self.stop_cascade_bot)
        self.kick_bot_stop_btn.pack(side="left")
        self.kick_auto = ctk.BooleanVar(value=False)  # compat
        self.kick_interact = ctk.BooleanVar(value=False)  # compat
        
        ctk.CTkLabel(kick_frame, text="🔗 Enlace del Streamer (Ej: https://kick.com/mrpoeta):", font=("Arial", 14, "bold"), text_color="white").pack(anchor="w", padx=30)
        self.kick_textbox = ctk.CTkTextbox(kick_frame, height=50)
        self.kick_textbox.pack(padx=30, pady=(0,20), fill="x")
        
        ctk.CTkLabel(kick_frame, text="📝 Tus Comentarios (Escribe uno por renglón):", font=("Arial", 14, "bold"), text_color="#A7F3D0").pack(anchor="w", padx=30)
        self.kick_chat_textbox = ctk.CTkTextbox(kick_frame, height=150)
        self.kick_chat_textbox.insert("1.0", "Holaaa\nLlegandooo\nSaludos a todos\nQue buen stream!")
        self.kick_chat_textbox.pack(padx=30, pady=(0,20), fill="both", expand=True)
        
        
        # Batch selector
        batch_frame = ctk.CTkFrame(kick_frame, fg_color="transparent")
        batch_frame.pack(fill="x", padx=30, pady=(0, 10))
        ctk.CTkLabel(batch_frame, text="Procesar de a (Lotes):", font=("Arial", 12, "bold"), text_color="white").pack(side="left")
        self.batch_size_var = ctk.StringVar(value="Todos")
        ctk.CTkOptionMenu(batch_frame, values=["1", "2", "4", "5", "10", "20", "30", "40", "Todos"], variable=self.batch_size_var, width=80).pack(side="left", padx=10)

        btn_frame = ctk.CTkFrame(kick_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20, padx=30)
        
        self.btn_kick_login = ctk.CTkButton(btn_frame, text="🔑 1. Pre-Check (Loguear Cuentas)", fg_color="#2563EB", hover_color="#1D4ED8", height=40, font=("Arial", 14, "bold"), command=self.start_kick_google_login)
        self.btn_kick_login.pack(side="left")
        
        self.btn_kick = ctk.CTkButton(btn_frame, text="▶ 2. Inyectar Visitas Kick", fg_color="#16A34A", hover_color="#15803D", height=40, font=("Arial", 14, "bold"), command=self.inject_kick)
        self.btn_kick.pack(side="right", padx=(10, 0))
        
        self.btn_kick_chat = ctk.CTkButton(btn_frame, text="💬 Forzar Comentario Ahora", fg_color="#9333EA", hover_color="#7E22CE", height=40, font=("Arial", 14, "bold"), command=self.force_kick_chat)
        self.btn_kick_chat.pack(side="right")
        
        bottom_frame = ctk.CTkFrame(self.tab_social, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=10)
        ctk.CTkButton(bottom_frame, text="💾 Guardar Cambios", fg_color="#10B981", command=self.save_config).pack(side="left", padx=20)
        ctk.CTkButton(bottom_frame, text="🛑 Detener Bots Kick", fg_color="#DC2626", hover_color="#991B1B", command=self.stop_social_bots).pack(side="right", padx=20)

    def build_ig_tab(self):
        self.tab_ig.grid_columnconfigure(0, weight=1)
        main_frame = ctk.CTkScrollableFrame(self.tab_ig, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ig_frame = ctk.CTkFrame(main_frame, fg_color="#831843", corner_radius=12)
        ig_frame.pack(fill="both", expand=True, pady=10)
        
        ctk.CTkLabel(ig_frame, text="📸 Instagram Automator", font=("Arial", 24, "bold"), text_color="#F472B6").pack(pady=20)
        
        self.ig_auto = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(ig_frame, text=" ❤️ Auto-Like y Swipe de Reels", font=("Arial", 14, "bold"), text_color="white", variable=self.ig_auto).pack(anchor="w", padx=30, pady=5)
        
        self.ig_interact = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(ig_frame, text=" 💬 Interacción Avanzada (Comentar/Guardar)", font=("Arial", 13), text_color="white", variable=self.ig_interact).pack(anchor="w", padx=30, pady=(0,20))
        
        ctk.CTkLabel(ig_frame, text="🔗 Enlace del Perfil o Reel:", font=("Arial", 14, "bold"), text_color="white").pack(anchor="w", padx=30)
        self.ig_textbox = ctk.CTkTextbox(ig_frame, height=50)
        self.ig_textbox.pack(padx=30, pady=(0,20), fill="x")
        
        btn_frame = ctk.CTkFrame(ig_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20, padx=30)
        
        btn_ig = ctk.CTkButton(btn_frame, text="▶ Iniciar Instagram", fg_color="#BE185D", height=40, font=("Arial", 14, "bold"), command=self.inject_ig)
        btn_ig.pack(side="right")
        
        bottom_frame = ctk.CTkFrame(self.tab_ig, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=10)
        ctk.CTkButton(bottom_frame, text="🛑 Detener Bots IG", fg_color="#DC2626", hover_color="#991B1B", command=self.stop_social_bots).pack(side="right", padx=20)

    def build_labs_tab(self):
        self.tab_labs.grid_columnconfigure(0, weight=1)
        main_frame = ctk.CTkFrame(self.tab_labs, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(main_frame, text="🧪 Laboratorio de Redes Sociales", font=("Arial", 28, "bold"), text_color="white").pack(pady=40)
        
        ctk.CTkLabel(main_frame, text="Próximas Integraciones:", font=("Arial", 18, "bold"), text_color="#9CA3AF").pack(pady=10)
        
        tk_frame = ctk.CTkFrame(main_frame, fg_color="#1F2937", corner_radius=8)
        tk_frame.pack(fill="x", padx=100, pady=10)
        ctk.CTkLabel(tk_frame, text="🎵 TikTok (En Desarrollo)", font=("Arial", 16), text_color="white").pack(pady=15)
        
        fb_frame = ctk.CTkFrame(main_frame, fg_color="#1F2937", corner_radius=8)
        fb_frame.pack(fill="x", padx=100, pady=10)
        ctk.CTkLabel(fb_frame, text="📘 Facebook (Planificado)", font=("Arial", 16), text_color="white").pack(pady=15)
        
        x_frame = ctk.CTkFrame(main_frame, fg_color="#1F2937", corner_radius=8)
        x_frame.pack(fill="x", padx=100, pady=10)
        ctk.CTkLabel(x_frame, text="✖ X / Twitter (Planificado)", font=("Arial", 16), text_color="white").pack(pady=15)

    def stop_social_bots(self):
        self.stop_social_threads = True
        self.log_msg("🛑 Iniciando detención controlada de Redes...", "warn")
        
        # Crear un modal que bloquee la UI
        import customtkinter as ctk
        modal = ctk.CTkToplevel(self)
        modal.title("Deteniendo Redes")
        modal.geometry("400x200")
        modal.attributes('-topmost', True)
        modal.grab_set() # Bloquear la ventana principal
        modal.protocol("WM_DELETE_WINDOW", lambda: None) # Deshabilitar boton X
        
        lbl = ctk.CTkLabel(modal, text="Deteniendo dispositivos uno por uno...\nPor favor espera, no cierres la app.", font=("Arial", 14, "bold"))
        lbl.pack(expand=True)
        
        import threading
        import time
        
        def _stop_process():
            if hasattr(self, 'engine') and getattr(self.engine, 'active_devices', []):
                total = len(self.engine.active_devices)
                for i, dev in enumerate(self.engine.active_devices):
                    s = dev['serial']
                    lbl.configure(text=f"Deteniendo dispositivo {i+1} de {total}...\n[{s[-4:]}]")
                    self.adb.run_command(["shell", "am", "force-stop", "com.instagram.android"], s)
                    self.adb.run_command(["shell", "am", "force-stop", "com.kick.mobile"], s)
                    self.adb.run_command(["shell", "input", "keyevent", "3"], s)
                    time.sleep(2) # Pausa de 2 segundos entre cada telefono para evitar que ADB colapse
            
            # Al terminar
            lbl.configure(text="✅ Todas las redes detenidas.\nCelulares listos.")
            time.sleep(1.5)
            modal.grab_release()
            modal.destroy()
            self.log_msg("✅ Redes detenidas con éxito y de forma segura.", "success")
            
        threading.Thread(target=_stop_process, daemon=True).start()

    def interact_ig_post(self, s):
        self.log_msg(f"Iniciando interacción avanzada en {s}...", "info")
        import random
        # 1. Intentar ver si ya tiene like mediante XML
        self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], s)
        import os
        local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"dump_{s}.xml")
        self.adb.run_command(["pull", "/sdcard/window_dump.xml", local_path], s)
        
        has_like = False
        import xml.etree.ElementTree as ET
        try:
            tree = ET.parse(local_path)
            root = tree.getroot()
            os.remove(local_path)
            for node in root.iter():
                desc = node.get("content-desc", "").lower()
                text = node.get("text", "").lower()
                if "ya no me gusta" in desc or "ya no me gusta" in text or "unlike" in desc:
                    has_like = True
                    break
        except Exception:
            pass

        # 2. Dar Like si no tiene
        if has_like:
            self.log_msg(f"✅ El post en {s} ya tiene Like. Omitiendo...", "info")
        else:
            self.log_msg(f"Dando Like inteligente en {s}...", "info")
            click_like = self.find_and_click_by_text(s, ["me gusta", "like"])
            if not click_like:
                self.adb.run_command(["shell", "input", "tap", "50", "1050"], s)
            time.sleep(1)

        # 3. Comentar (Ocasional)
        if random.random() < 0.3: # 30% de probabilidad
            self.log_msg("Escribiendo comentario...", "info")
            click_comment = self.find_and_click_by_text(s, ["comentar", "comment"])
            if not click_comment:
                self.adb.run_command(["shell", "input", "tap", "350", "1050"], s)
            time.sleep(2)
            
            # Escribir comentario
            comments = ["Fuegooo 🔥", "Genial!", "👏👏👏", "Wow", "Excelente"]
            comment = random.choice(comments)
            # Presionar teclado virtual
            for char in comment:
                self.adb.run_command(["shell", "input", "text", char], s)
                time.sleep(0.1)
            time.sleep(1)
            # Enviar (enter o boton)
            self.adb.run_command(["shell", "input", "keyevent", "66"], s)
            time.sleep(2)
            # Back para cerrar panel de comentarios
            self.adb.run_command(["shell", "input", "keyevent", "4"], s)
            time.sleep(1)

        # 4. Guardar (Ocasional)
        if random.random() < 0.5:
            self.log_msg("Guardando post...", "info")
            click_save = self.find_and_click_by_text(s, ["guardar", "save"])
            if not click_save:
                self.adb.run_command(["shell", "input", "tap", "650", "1050"], s)
            time.sleep(1)

        # 5. Compartir en Historia (Ocasional)
        if random.random() < 0.2: # 20% de probabilidad
            self.log_msg("Compartiendo en Historia...", "info")
            click_share = self.find_and_click_by_text(s, ["enviar", "compartir", "share", "send"])
            if not click_share:
                # Botón de enviar típico (Avioncito)
                self.adb.run_command(["shell", "input", "tap", "650", "950"], s)
            time.sleep(3)
            
            # Tocar 'Agregar a historia' (suele estar abajo a la izquierda en el popup)
            click_add = self.find_and_click_by_text(s, ["agregar a historia", "add to story"])
            if not click_add:
                self.adb.run_command(["shell", "input", "tap", "150", "1100"], s)
            time.sleep(6) # Esperar que cargue el editor de historias
            
            # Tocar 'Tu historia' para publicar
            click_tu_historia = self.find_and_click_by_text(s, ["tu historia", "your story"])
            if not click_tu_historia:
                # Coordenada típica del botón 'Tu historia'
                self.adb.run_command(["shell", "input", "tap", "160", "1260"], s)
            time.sleep(4)
            self.log_msg("✅ Compartido en historia exitosamente.", "success")


    def inject_ig(self):
        self.stop_social_threads = False
        if not hasattr(self, 'engine') or not getattr(self.engine, 'active_devices', []):
            self.log_msg("⚠️ El túnel no está iniciado.", "warn")
            return
        urls = [u.strip() for u in self.ig_textbox.get("1.0", "end").strip().split('\n') if u.strip()]
        if not urls:
            self.log_msg("⚠️ La caja de texto de Kick está vacía. Pega un link primero.", "warn")
            return
        import random
        import re
        
        def _bot():
            for dev in self.engine.active_devices:
                if getattr(self, "stop_social_threads", False): break
                url = random.choice(urls)
                s = dev['serial']
                
                # Extraer username y construir deep link
                username = ""
                m = re.search(r"instagram\.com/([^/?]+)", url)
                if m:
                    username = m.group(1)
                    deep_link = f"instagram://user?username={username}"
                else:
                    deep_link = url # Fallback
                
                self.log_msg(f"Abriendo IG: {username} en {s}...")
                
                # Cierra otras apps y refresca IG
                self._force_portrait(s)
                self._cleanup_background_apps(s, exclude_pkg="com.instagram.android")
                self.adb.run_command(["shell", "am", "force-stop", "com.instagram.android"], s)
                time.sleep(1)
                
                # Inicia el Deep Link nativo
                self.adb.run_command(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"'{deep_link}'", "com.instagram.android"], s)
                
                if self.ig_auto.get():
                    self.log_msg(f"Esperando carga del perfil en {s}...", "info")
                    time.sleep(15) # Espera buena carga
                    
                    self.log_msg(f"Buscando botón 'Seguir' en {s}...", "info")
                    click_seguir = self.find_and_click_by_text(s, [f"Seguir a {username}", "Seguir", "Follow"])
                    if click_seguir:
                        self.log_msg(f"✅ ¡Follow enviado a {username}!", "success")
                        time.sleep(2)
                    
                    # Decidir aleatoriamente entre Historias o Publicaciones para no chocar
                    modo = random.choice(["historias", "publicaciones"])
                    self.log_msg(f"Decidió interactuar con: {modo}", "info")
                    
                    if modo == "historias":
                        click_foto = self.find_and_click_by_text(s, ["Foto del perfil", "Profile photo", "Historia vista", "Historia no vista", "Historia de"])
                        if click_foto:
                            self.log_msg(f"✅ Viendo historias de {username}", "success")
                            time.sleep(30)
                        else:
                            self.log_msg("No hay historias disponibles. Cancelando.", "warn")
                    else:
                        # Modo publicaciones / Reels
                        self.log_msg(f"Deslizando para buscar publicaciones de {username}", "info")
                        # Hacemos 2 swipes largos para asegurar pasar las Historias Destacadas (Highlights)
                        self.adb.run_command(["shell", "input", "swipe", "360", "1200", "360", "200"], s)
                        time.sleep(1)
                        self.adb.run_command(["shell", "input", "swipe", "360", "1200", "360", "200"], s)
                        time.sleep(2)
                        
                        # Buscamos específicamente un cuadro de la cuadrícula de publicaciones o reels
                        click_post = self.find_and_click_by_text(s, ["columna 1", "columna 2", "column 1"])
                        if not click_post:
                            self.log_msg(f"Usando toque de respaldo para abrir reel...", "warn")
                            # Toque de respaldo más abajo para asegurar tocar la cuadrícula y no las historias destacadas
                            self.adb.run_command(["shell", "input", "tap", "200", "850"], s)
                        
                        self.log_msg(f"✅ Viendo publicaciones de {username}", "success")
                        time.sleep(4)
                        
                        if getattr(self, 'ig_interact', None) and self.ig_interact.get():
                            self.interact_ig_post(s)
                        
                        # Swipe Up suave y largo (de abajo hacia arriba)
                        self.adb.run_command(["shell", "input", "swipe", "360", "1100", "360", "150"], s)
                        
                time.sleep(2)
        threading.Thread(target=_bot, daemon=True).start()
        self.log_msg("✨ Inyectando Instagram con automatización Inteligente...", "info")

    def _kick_search_and_enter(self, serial, streamer_name, is_slow=False):
        import time
        def s_sleep(base_time):
            time.sleep(base_time * 2.5 if is_slow else base_time)
            
        self.log_msg(f"🕵️ Iniciando Búsqueda Humana en Kick para: {streamer_name}...", "info")
        
        self._cleanup_background_apps(serial, exclude_pkg="com.kick.mobile")
        self.adb.run_command(["shell", "am", "force-stop", "com.kick.mobile"], serial)
        s_sleep(1.0)
        
        self.adb.run_command(["shell", "am", "start", "-n", "com.kick.mobile/com.kick.mobile.MainActivity"], serial)
        self.log_msg("Esperando a que Kick cargue...", "info")
        s_sleep(10.0)
        
        # 1. Dismiss survey if exists
        self.find_and_click_by_text(serial, ["maybe later", "quizás más tarde", "omitir", "skip", "no thanks"])
        s_sleep(2.0)
        
        # 2. Click Search (Lupa)
        if not self.find_and_click_by_text(serial, ["search", "buscar"]):
            self.log_msg("No se halló el botón buscar por texto. Usando tap ciego en menú inferior...", "warn")
            self.adb.run_command(["shell", "input", "tap", "380", "900"], serial)
        
        s_sleep(3.0)
        
        # 3. Type streamer name
        self.log_msg(f"Escribiendo '{streamer_name}'...", "info")
        for char in streamer_name:
            self.adb.run_command(["shell", "input", "text", char], serial)
            time.sleep(0.1)
            
        s_sleep(2.0)
        
        # Press ENTER on keyboard to search
        self.adb.run_command(["shell", "input", "keyevent", "66"], serial)
        s_sleep(4.0)
        
        # 4. Click the top result
        if not self.find_and_click_by_text(serial, [streamer_name, "live"]):
            self.log_msg("Tap ciego en primer resultado...", "warn")
            self.adb.run_command(["shell", "input", "tap", "240", "180"], serial)
            
        s_sleep(6.0)
        self.log_msg(f"✅ Búsqueda terminada. Entrando al canal {streamer_name}.", "success")
        return True

    def _kick_chat_engine(self, serial):
        """Motor de chat inteligente: lee el chat, elige un comentario y lo envia via interact_kick_stream."""
        import random, time
        if not getattr(self, 'kick_interact', None) or not self.kick_interact.get():
            return
        
        # 1. Leer pantalla actual del chat
        root = getattr(self, 'pull_and_parse', lambda x: None)(serial)
        chat_text = ""
        if root is not None:
            chat_text = " ".join([n.get("text", "").lower() for n in root.iter("node")])
        
        # 2. Elegir personalidad (consistente por dispositivo)
        if not hasattr(self, 'kick_personalities'):
            self.kick_personalities = {}
        if serial not in self.kick_personalities:
            self.kick_personalities[serial] = random.choice(["Fan", "Troll", "Spammer"])
        perfil = self.kick_personalities[serial]
        self.log_msg(f" [{serial[-4:]}] Chat Engine ({perfil})...", "info")
        
        # 3. Analizar palabras clave del chat y elegir respuesta
        comment = ""
        if "hora" in chat_text or "time" in chat_text:
            comment = {"Fan": "que buena hora para un stream!", "Troll": "ya es tarde, vete a dormir zzz", "Spammer": "time is money !drop"}.get(perfil, "")
        elif "manco" in chat_text or "noob" in chat_text or "fail" in chat_text:
            comment = {"Fan": "no le hagas caso, juegas bien bro!", "Troll": "literalmente el peor jugador jajaja", "Spammer": "F en el chat"}.get(perfil, "")
        elif "hola" in chat_text or "saludos" in chat_text:
            comment = {"Fan": "Hola chat!! un abrazo a todos", "Troll": "nadie te saludo xd", "Spammer": "hola !discord"}.get(perfil, "")
        elif "juego" in chat_text or "game" in chat_text:
            comment = {"Fan": "este juego es una obra maestra", "Troll": "juego muerto (dead game)", "Spammer": "!game"}.get(perfil, "")
        
        # 4. Fallback: comentario generico
        if not comment:
            pools = {
                "Fan": ["W stream", "bro you are insane", "love this", "best streamer ever", "lets gooo", "huge W"],
                "Troll": ["L", "boring af", "skill issue", "go next", "cringe", "zzz"],
                "Spammer": ["!drop", "!discord", "!points", "!socials"]
            }
            comment = random.choice(pools.get(perfil, ["gg"]))
        
        self.log_msg(f" [{serial[-4:]}] Enviando: '{comment}'", "info")
        
        # 5. Inyectar el comentario usando el mismo motor probado
        # Temporalmente sobreescribimos el mensaje aleatorio con el elegido
        original_get = self.get_random_kick_message
        self.get_random_kick_message = lambda: comment
        try:
            self.interact_kick_stream(serial)
        finally:
            self.get_random_kick_message = original_get

    def _continuous_kick_chat_loop(self):
        import time
        import random
        while True:
            if getattr(self, "stop_social_threads", False):
                self._kick_chat_thread_active = False
                break
                
            time.sleep(120) # Pausa de 2 minutos antes de cada ciclo global
            
            if not hasattr(self, 'engine') or not self.engine.active_devices:
                continue
                
            self.log_msg("🗣️ [KICK CHAT] Iniciando ciclo de interacciones globales...", "info")
            
            for dev in list(self.engine.active_devices):
                if getattr(self, "stop_social_threads", False):
                    break
                    
                s = dev['serial']
                if self.is_device_locked(s):
                    continue
                
                # Check si está en la app de kick
                out_tuple = self.adb.run_command(["shell", "dumpsys", "window", "windows", "|", "grep", "-E", "'mCurrentFocus|mFocusedApp'"], s)
                out = out_tuple[0] if isinstance(out_tuple, tuple) else out_tuple
                if out and "com.kick.mobile" in out:
                    root = getattr(self, 'pull_and_parse', lambda x: None)(s)
                    if root is not None:
                        texts = [n.get("text", "").lower() for n in root.iter("node")]
                        if "go back" in texts or "volver" in texts or "featured creators" in texts or "top live categories" in texts:
                            self.log_msg(f"🚨 [{s[-4:]}] App trabada o en menú antes de chatear. Ignorando chat para que el Rescatista actúe.", "warn")
                        else:
                            if random.randint(1, 100) <= 60: # 60% prob de hablar en cada ciclo
                                self.log_msg(f"💬 [{s[-4:]}] Comentando en Kick...", "info")
                                self._kick_chat_engine(s)
                
                time.sleep(10) # 10 segundos de espera entre celular y celular para no saturar

    def _manual_kick_rescue(self):
        """Boton manual de rescate Kick"""
        if not hasattr(self, 'engine') or not self.engine.active_devices:
            return
            
        import threading
        def _rescue_process():
            self.log_msg("🚑 Iniciando Rescate Manual de Kick...", "warn")
            for dev in list(self.engine.active_devices):
                s = dev['serial']
                
                if self.is_device_locked(s): continue
                
                out_tuple = self.adb.run_command(["shell", "dumpsys", "window", "windows", "|", "grep", "-E", "'mCurrentFocus|mFocusedApp'"], s)
                out = out_tuple[0] if isinstance(out_tuple, tuple) else out_tuple
                if out and "com.kick.mobile" in out:
                    root = getattr(self, 'pull_and_parse', lambda x: None)(s)
                    if root is not None:
                        texts = [n.get("text", "").lower() for n in root.iter("node")]
                        needs_rescue = False
                        if "featured creators" in texts or "top live categories" in texts:
                            needs_rescue = True
                        elif "go back" in texts or "volver" in texts:
                            self.log_msg(f"💥 [{s[-4:]}] Error de Kick ('Go Back'). Presionando...", "warn")
                            self.find_and_click_by_text(s, ["go back", "volver"])
                            time.sleep(2)
                            needs_rescue = True
                            
                        if needs_rescue:
                            self.log_msg(f"🔍 [{s[-4:]}] Extraviado. Rescatando e inyectando de nuevo...", "warn")
                            urls = [u.strip() for u in self.kick_textbox.get("1.0", "end").strip().split("\n") if u.strip()]
                            if urls:
                                import random
                                streamer = random.choice(urls).rstrip('/').split('/')[-1]
                                self._kick_search_and_enter(s, streamer, is_slow=False)
                            time.sleep(5)
            self.log_msg("✅ Rescate Manual Completado.", "success")
            
        threading.Thread(target=_rescue_process, daemon=True).start()


    def force_kick_chat(self):
        """Fuerza a todos los dispositivos a buscar la caja de chat y enviar un comentario"""
        if not hasattr(self, 'engine') or not getattr(self.engine, 'active_devices', []):
            self.log_msg(" [Error] No hay dispositivos activos. Inicia el túnel.", "error")
            return
            
        import threading
        if hasattr(self, 'btn_kick_chat'):
            self.btn_kick_chat.configure(text=" ⏳ Forzando Comentarios...", fg_color="#F59E0B")
            
        def _force():
            from concurrent.futures import ThreadPoolExecutor
            
            batch_size = 1
            if hasattr(self, 'batch_size_var'):
                val = self.batch_size_var.get()
                if val == "Todos":
                    batch_size = len(self.engine.active_devices)
                else:
                    try: batch_size = int(val)
                    except: batch_size = 1
            else:
                batch_size = len(self.engine.active_devices)
                
            def force_dev(dev):
                s = dev['serial']
                self.log_msg(f" [Kick] Forzando comentario manual en {s[-4:]}...", "info")
                self.interact_kick_stream(s)

            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                executor.map(force_dev, self.engine.active_devices)
                
            self.log_msg(" [Kick] Fuerza de Comentarios Terminada.", "success")
            if hasattr(self, 'btn_kick_chat'):
                self.after(0, lambda: self.btn_kick_chat.configure(text=" Forzar Comentario Ahora", fg_color="#9333EA"))
                
        threading.Thread(target=_force, daemon=True).start()

    def get_random_kick_message(self):
        import random
        txt = self.kick_chat_textbox.get("1.0", "end-1c").strip()
        if not txt:
            messages = ["Holaaa", "Llegandooo", "Dejando mi apoyo!", "Buenaaas", "Saludos!!", "Epico!!"]
        else:
            messages = [line.strip() for line in txt.split("\n") if line.strip()]
        return random.choice(messages)

    def _type_text_human(self, serial, text):
        import time
        # Caracteres especiales y espacios fallan en React Native con ADB normal
        # Para espacios usaremos el keyevent 62 (SPACE)
        for char in text:
            if char == " ":
                self.adb.run_command(["shell", "input", "keyevent", "62"], serial)
            else:
                # Escapar caracteres
                safe_char = char.replace("\\", "\\\\").replace("\"", "\\\"").replace("'", "\\'")
                safe_char = safe_char.replace(" ", "%s").replace("&", "\\&").replace(";", "\\;")
                safe_char = safe_char.replace("(", "\\(").replace(")", "\\)").replace("|", "\\|")
                self.adb.run_command(["shell", "input", "text", safe_char], serial)
            time.sleep(0.05)

    def start_cascade_bot(self):
        """Inicia el bot de comentarios en cascada."""
        import threading
        if getattr(self, '_cascade_running', False):
            self.log_msg(" [Bot] Ya esta corriendo. Usa DETENER BOT primero.", "warn")
            return
        if not hasattr(self, 'engine') or not getattr(self.engine, 'active_devices', []):
            self.log_msg(" [Bot] No hay dispositivos activos. Inicia el tunel primero.", "error")
            return
        urls = [u.strip() for u in self.kick_textbox.get("1.0", "end").strip().split('\n') if u.strip()]
        if not urls:
            self.log_msg(" [Bot] Pega al menos un link de Kick primero.", "warn")
            return
        self._cascade_running = True
        self.log_msg(" [Bot] Bot en Cascada INICIADO.", "info")
        
        if hasattr(self, 'kick_bot_start_btn'):
            self.kick_bot_start_btn.configure(text=" 🟢 CASCADA ACTIVA", fg_color="#F59E0B")
            
        threading.Thread(target=self._cascade_loop, daemon=True).start()

    def stop_cascade_bot(self):
        """Detiene el bot de comentarios en cascada."""
        self._cascade_running = False
        self.log_msg(" [Bot] Bot en Cascada DETENIDO.", "warn")
        if hasattr(self, 'kick_bot_start_btn'):
            self.kick_bot_start_btn.configure(text=" INICIAR BOT", fg_color="#16A34A")

    def _cascade_loop(self):
        import time
        import random
        from concurrent.futures import ThreadPoolExecutor
        
        while getattr(self, '_cascade_running', False):
            devices = getattr(self.engine, 'active_devices', [])
            if not devices:
                self.log_msg(" [Bot] Sin dispositivos. Esperando...", "warn")
                time.sleep(30)
                continue

            interval_str = self.kick_bot_interval.get()
            interval_sec = int(interval_str.replace(" min", "")) * 60

            batch_size = 1
            if hasattr(self, 'batch_size_var'):
                val = self.batch_size_var.get()
                if val == "Todos": batch_size = len(devices)
                else:
                    try: batch_size = int(val)
                    except: batch_size = 1

            # Dividir dispositivos en lotes
            for i in range(0, len(devices), batch_size):
                if not getattr(self, '_cascade_running', False): break
                
                batch = devices[i:i+batch_size]
                
                def process_dev(dev):
                    if not getattr(self, '_cascade_running', False): return
                    s = dev['serial']
                    
                    do_comments = getattr(self, 'kick_bot_type_comments', None) and self.kick_bot_type_comments.get()
                    do_emojis = getattr(self, 'kick_bot_type_emojis', None) and self.kick_bot_type_emojis.get()
                    
                    if not do_comments and not do_emojis:
                        self.log_msg(f" [Bot] Advertencia: Ni texto ni emojis seleccionados.", "warn")
                        return

                    try:
                        if do_comments:
                            self.log_msg(f" [Bot] Enviando Texto en {s[-4:]}...", "info")
                            self.interact_kick_stream(s)
                            if do_emojis:
                                time.sleep(3) # Pausa breve si va a mandar ambos
                                
                        if do_emojis:
                            self.log_msg(f" [Bot] Enviando Emoji en {s[-4:]}...", "info")
                            self.send_kick_emote(s)
                            
                    except Exception as e:
                        self.log_msg(f" [Bot] Error en {s[-4:]}: {e}", "error")
                
                with ThreadPoolExecutor(max_workers=batch_size) as executor:
                    executor.map(process_dev, batch)

                if not getattr(self, '_cascade_running', False): break

                # Esperar intervalo antes del proximo lote
                self.log_msg(f" [Bot] Lote terminado. Esperando {interval_str}...", "info")
                for _ in range(interval_sec // 5):
                    if not getattr(self, '_cascade_running', False): break
                    time.sleep(5)

        self.log_msg(" [Bot] Loop terminado.", "info")

    def interact_kick_stream(self, s):
        import time
        import re
        
        # --- Paso 1: Medir pantalla real del dispositivo ---
        stdout, _, _ = self.adb.run_command(["shell", "wm", "size"], s)
        width, height = 480, 960
        match = re.search(r"(\d+)x(\d+)", stdout or "")
        if match:
            width, height = int(match.group(1)), int(match.group(2))
        self.log_msg(f" [{s[-4:]}] Pantalla: {width}x{height}. Escaneando Kick...", "info")
        
        # --- Paso 2: Despertar pantalla ---
        self.adb.run_command(["shell", "input", "tap", str(width//2), str(height//2)], s)
        time.sleep(1.0)
        
        # --- Paso 3: Escanear UI hasta 3 veces para encontrar la barra de chat ---
        chat_x, chat_y = None, None
        
        for intento in range(3):
            root = getattr(self, 'pull_and_parse', lambda x: None)(s)
            
            if root is not None:
                with open('kick_debug.txt', 'w', encoding='utf-8') as dbg:
                    for n in root.iter('node'):
                        t = n.get('text', '')
                        d = n.get('content-desc', '')
                        b = n.get('bounds', '')
                        if t or d: dbg.write(f'T:{t} | D:{d} | B:{b}\n')
                
                # Guardar todos los elementos del tercio inferior para calcular
                bottom_elements = {}
                lower_third = height * 0.7
                
                for n in root.iter("node"):
                    text_val = n.get("text", "").lower()
                    desc_val = n.get("content-desc", "").lower()
                    bounds = n.get("bounds", "")
                    if not bounds: continue
                    coords = [int(c) for c in bounds.replace("][", ",").replace("[", "").replace("]", "").split(",")]
                    cx = (coords[0] + coords[2]) // 2
                    cy = (coords[1] + coords[3]) // 2
                    
                    # Solo elementos en el tercio inferior de la pantalla
                    if cy < lower_third: continue
                    
                    # Prioridad 1: caja de texto directamente
                    if text_val in ["enviar mensaje", "send a message", "cargando...", "cargando", "loading..."]:
                        chat_x, chat_y = cx, cy
                        self.log_msg(f" [{s[-4:]}] ✅ Caja encontrada ('{text_val}') en {cx},{cy}", "info")
                        break
                    
                    # Prioridad 2: boton emote -> caja esta a su izquierda
                    if desc_val == "emote" and "emote" not in bottom_elements:
                        bottom_elements["emote"] = (coords[0], cy)  # borde izquierdo del emote
                    
                    # Prioridad 3: boton send -> caja esta a su izquierda
                    if desc_val == "send" and "send" not in bottom_elements:
                        bottom_elements["send"] = (coords[0], cy)  # borde izquierdo del send
                    
                    # Prioridad 4: boton identity (foto de perfil) -> caja esta a su derecha
                    if desc_val == "identity" and "identity" not in bottom_elements:
                        bottom_elements["identity"] = (coords[2], cy)  # borde derecho del identity
                
                # Calcular posicion de la caja segun lo que encontramos
                if chat_x is None:
                    if "emote" in bottom_elements:
                        # La caja esta entre el identity y el emote
                        ex, ey = bottom_elements["emote"]
                        chat_x = ex - 80  # 80px a la izquierda del emote
                        chat_y = ey
                        self.log_msg(f" [{s[-4:]}] ✅ Caja calculada (via emote) en {chat_x},{chat_y}", "info")
                    elif "send" in bottom_elements:
                        sx, sy = bottom_elements["send"]
                        chat_x = sx - 150  # a la izquierda del boton send
                        chat_y = sy
                        self.log_msg(f" [{s[-4:]}] ✅ Caja calculada (via send) en {chat_x},{chat_y}", "info")
                    elif "identity" in bottom_elements:
                        ix, iy = bottom_elements["identity"]
                        chat_x = ix + 80  # a la derecha del identity
                        chat_y = iy
                        self.log_msg(f" [{s[-4:]}] ✅ Caja calculada (via identity) en {chat_x},{chat_y}", "info")
            
            if chat_x is not None:
                break
            else:
                if intento < 2:
                    self.log_msg(f" [{s[-4:]}] ⏳ Nada visible aun (intento {intento+1}/3). Esperando 10s...", "warn")
                    time.sleep(10)
                    self.adb.run_command(["shell", "input", "tap", str(width//2), str(height//2)], s)
                    time.sleep(1)
                else:
                    # Ultimo recurso: proporcional a la pantalla real
                    chat_x = int(width * 0.43)
                    chat_y = int(height * 0.82)
                    self.log_msg(f" [{s[-4:]}] ❌ Scan fallido x3. Calculando proporcional: {chat_x},{chat_y}", "error")
        
        # --- Paso 4: Tocar y verificar teclado ---
        keyboard_open = False
        for tap_intento in range(2):
            self.adb.run_command(["shell", "input", "tap", str(chat_x), str(chat_y)], s)
            time.sleep(2.5)
            try:
                out, _, _ = self.adb.run_command(["shell", "dumpsys", "input_method"], s)
                if out and ("mInputShown=true" in out or "mActive=true" in out):
                    keyboard_open = True
                    break
            except Exception:
                pass
            if tap_intento == 0 and not keyboard_open:
                self.log_msg(f" [{s[-4:]}] ⏳ Teclado no salio. Reintentando...", "warn")
        
        if keyboard_open:
            self.log_msg(f" [{s[-4:]}] ✅ Teclado abierto.", "info")
        else:
            self.log_msg(f" [{s[-4:]}] ❌ Teclado no detectable. Escribiendo igual...", "error")
        
        # --- Paso 5: Escribir y enviar ---
        msg = self.get_random_kick_message()
        self.log_msg(f" [{s[-4:]}] ✍️ Mensaje: {msg}", "info")
        self._type_text_human(s, msg)
        time.sleep(0.5)
        
        # ENTER envia el mensaje (suficiente, no hace falta buscar boton send despues)
        self.adb.run_command(["shell", "input", "keyevent", "66"], s)
        time.sleep(0.8)
        
        # ESCAPE baja el teclado sin minimizar el video ni tocar nada mas
        self.adb.run_command(["shell", "input", "keyevent", "111"], s)
        self.log_msg(f" [{s[-4:]}] ✅ Mensaje enviado.", "info")

    def send_kick_emote(self, s):
        """Usa la barra rapida de emojis verdes justo arriba de la caja de chat."""
        import time
        import re
        import random
        
        stdout, _, _ = self.adb.run_command(["shell", "wm", "size"], s)
        width, height = 480, 960
        match = re.search(r"(\d+)x(\d+)", stdout or "")
        if match:
            width, height = int(match.group(1)), int(match.group(2))
        
        self.log_msg(f" [{s[-4:]}] Escaneando para enviar Emoji Verde...", "info")
        
        # Despertar
        self.adb.run_command(["shell", "input", "tap", str(width//2), str(height//2)], s)
        time.sleep(1.0)
        
        chat_x, chat_y = None, None
        send_btn_x, send_btn_y = None, None
        
        for intento in range(3):
            root = getattr(self, 'pull_and_parse', lambda x: None)(s)
            if root is not None:
                lower_third = height * 0.6
                for n in root.iter("node"):
                    text_val = n.get("text", "").lower()
                    desc_val = n.get("content-desc", "").lower()
                    bounds = n.get("bounds", "")
                    if not bounds: continue
                    coords = [int(c) for c in bounds.replace("][", ",").replace("[", "").replace("]", "").split(",")]
                    cx = (coords[0] + coords[2]) // 2
                    cy = (coords[1] + coords[3]) // 2
                    
                    if cy < lower_third: continue
                    
                    # Buscar caja de chat
                    if text_val in ["enviar mensaje", "send a message", "cargando...", "loading..."]:
                        chat_x, chat_y = cx, cy
                        
                    # Buscar boton de enviar (flechita)
                    if desc_val == "send":
                        send_btn_x, send_btn_y = cx, cy
                        
            if chat_x and chat_y:
                break
                
            self.log_msg(f" [{s[-4:]}]  Buscando chat para emojis... (Intento {intento+1}/3)", "warn")
            time.sleep(4)
            
        if not chat_y:
            self.log_msg(f" [{s[-4:]}] ❌ No se encontro la caja de chat para calcular los emojis.", "error")
            return
            
        # La barra de emojis rapidos esta aprox 70-90 pixeles (en 960p) arriba de la caja de chat
        offset_y = int(height * 0.08)
        quick_emote_y = chat_y - offset_y
        
        cantidad = random.randint(1, 2)
        self.log_msg(f" [{s[-4:]}] ✅ Tocando {cantidad} emojis rapidos (Barra superior)...", "success")
        
        for _ in range(cantidad):
            # Tocar un emoji aleatorio en el ancho de la pantalla
            random_x = random.randint(int(width * 0.2), int(width * 0.8))
            self.adb.run_command(["shell", "input", "tap", str(random_x), str(quick_emote_y)], s)
            time.sleep(0.5)
            
        time.sleep(1.0)
        
        # Volvemos a buscar el boton enviar por si no lo capturamos antes
        if not send_btn_x:
            root = getattr(self, 'pull_and_parse', lambda x: None)(s)
            if root is not None:
                for n in root.iter("node"):
                    if n.get("content-desc", "").lower() == "send":
                        bounds = n.get("bounds", "")
                        if bounds:
                            coords = [int(c) for c in bounds.replace("][", ",").replace("[", "").replace("]", "").split(",")]
                            send_btn_x = (coords[0] + coords[2]) // 2
                            send_btn_y = (coords[1] + coords[3]) // 2
                            break
                            
        if send_btn_x and send_btn_y:
            self.adb.run_command(["shell", "input", "tap", str(send_btn_x), str(send_btn_y)], s)
        else:
            # Fallback: tocar a la derecha de la caja de chat (ahi suele estar el boton enviar)
            fallback_x = width - int(width * 0.08)
            self.adb.run_command(["shell", "input", "tap", str(fallback_x), str(chat_y)], s)
            
        self.log_msg(f" [{s[-4:]}] 🟢 Emoji Enviado Correctamente.", "success")

    def inject_kick(self):
        self.stop_social_threads = False
        if not hasattr(self, 'engine') or not getattr(self.engine, 'active_devices', []):
            self.log_msg(" El túnel no está iniciado.", "warn")
            return
        urls = [u.strip() for u in self.kick_textbox.get("1.0", "end").strip().split('\n') if u.strip()]
        if not urls:
            self.log_msg(" La caja de texto de Kick está vacía. Pega un link primero.", "warn")
            return
            
        import threading
        
        if hasattr(self, 'btn_kick'):
            self.btn_kick.configure(text=" 🟢 Inyectando Visitas...", fg_color="#F59E0B")
            
        def _bot():
            import random
            import time
            from concurrent.futures import ThreadPoolExecutor
            
            batch_size = 1
            if hasattr(self, 'batch_size_var'):
                val = self.batch_size_var.get()
                if val == "Todos":
                    batch_size = len(self.engine.active_devices)
                else:
                    try: batch_size = int(val)
                    except: batch_size = 1
            else:
                batch_size = len(self.engine.active_devices)

            def process_dev(dev):
                if getattr(self, "stop_social_threads", False): return
                url = random.choice(urls)
                s = dev['serial']
                self.log_msg(f"Abriendo Kick URL en {s}...", "info")
                
                self._cleanup_background_apps(s, exclude_pkg="com.kick.mobile")
                self.adb.run_command(["shell", "am", "force-stop", "com.kick.mobile"], s)
                time.sleep(1)
                
                self.adb.run_command(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"'{url}'", "com.kick.mobile"], s)
                self.log_msg(f"[{s[-4:]}] Esperando 20s a que cargue el stream...", "info")
                time.sleep(20)
                
                # Se envia comentario inicial opcionalmente si es necesario, lo quitamos para que sea mas limpio y el cascada haga el trabajo duro.
                # Pero el viejo si comentaba, llamando self.interact_kick_stream(s). 
                # Se deja solo abriendo la app. El chat en cascada hara los comentarios segun su timer.

            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                executor.map(process_dev, self.engine.active_devices)
                
            self.log_msg(" ✅ Inyección Kick Terminada.", "success")
            if hasattr(self, 'btn_kick'):
                self.after(0, lambda: self.btn_kick.configure(text=" 2. Inyectar Visitas Kick", fg_color="#16A34A"))

        threading.Thread(target=_bot, daemon=True).start()
        self.log_msg(" Iniciando hilos de inyección en lote...", "info")

    def build_accounts_tab(self):
        self.tab_accounts.grid_columnconfigure(0, weight=1)
        self.tab_accounts.grid_columnconfigure(1, weight=1)
        self.tab_accounts.grid_rowconfigure(0, weight=1)
        
        # Panel izquierdo (Controles y Logs)
        left_frame = ctk.CTkScrollableFrame(self.tab_accounts, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        ctk.CTkLabel(left_frame, text="🤖 Creador de Cuentas (Redes Sociales)", font=("Arial", 20, "bold"), text_color="#3B82F6").pack(pady=(0, 20))
        
        # Selector de Red
        self.acc_network_var = ctk.StringVar(value="Kick")
        net_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        net_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(net_frame, text="Red Social:", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        self.acc_network_combo = ctk.CTkOptionMenu(net_frame, values=["Kick", "Instagram"], variable=self.acc_network_var, width=150)
        self.acc_network_combo.pack(side="left", padx=5)

        # Formulario
        form_frame = ctk.CTkFrame(left_frame, fg_color="#1E293B", corner_radius=12)
        form_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(form_frame, text="Prefijo de Correo:", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(15, 0))
        self.acc_email_prefix_entry = ctk.CTkEntry(form_frame, placeholder_text="Ej: juan.perez")
        self.acc_email_prefix_entry.pack(fill="x", padx=20, pady=5)
        self.acc_email_prefix_entry.insert(0, "user")
        
        ctk.CTkLabel(form_frame, text="Dominio (@):", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(5, 0))
        self.acc_email_domain_entry = ctk.CTkEntry(form_frame, placeholder_text="Ej: gmail.com")
        self.acc_email_domain_entry.pack(fill="x", padx=20, pady=5)
        self.acc_email_domain_entry.insert(0, "gmail.com")
        
        ctk.CTkLabel(form_frame, text="Contraseña Base:", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(5, 0))
        self.acc_password_entry = ctk.CTkEntry(form_frame, placeholder_text="Mínimo 8 caracteres (Letras y Números)")
        self.acc_password_entry.pack(fill="x", padx=20, pady=(5, 20))
        self.acc_password_entry.insert(0, "Pass1234!")
        
        # Botones de Acción
        btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=15)
        
        self.btn_scan_acc = ctk.CTkButton(btn_frame, text="🔍 1. Refrescar Lista USB", fg_color="#3B82F6", hover_color="#2563EB", command=self.update_account_creator_devices, height=35)
        self.btn_scan_acc.pack(fill="x", pady=5)
        
        self.btn_create_acc = ctk.CTkButton(btn_frame, text="▶️ 2. Iniciar Creación de Cuentas (Solo Kick por ahora)", fg_color="#10B981", hover_color="#059669", command=self.start_kick_google_login, height=45, font=("Arial", 13, "bold"))
        self.btn_create_acc.pack(fill="x", pady=5)
        
        # Log del creador
        ctk.CTkLabel(left_frame, text="Registro de Actividad:", font=("Arial", 12, "bold"), text_color="#9CA3AF").pack(anchor="w", pady=(10, 5))
        self.acc_log_box = ctk.CTkTextbox(left_frame, height=180, font=("Consolas", 11))
        self.acc_log_box.pack(fill="both", expand=True)
        self.acc_log_box.insert("1.0", "Esperando ordenes...\n")
        
        # Panel derecho (Lista de dispositivos a usar)
        right_frame = ctk.CTkFrame(self.tab_accounts, fg_color="#0F172A", corner_radius=12)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        ctk.CTkLabel(right_frame, text="📱 Dispositivos para Creación", font=("Arial", 16, "bold")).pack(pady=15)
        
        self.acc_devices_scroll = ctk.CTkScrollableFrame(right_frame, fg_color="transparent")
        self.acc_devices_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.acc_device_checkboxes = {}

    def update_account_creator_devices(self):
        if not hasattr(self, 'acc_devices_frame'): return
        devices = getattr(self, 'scanned_devices', [])
        serials = [dev['serial'] for dev in devices]
        
        # Guardar selecciones actuales
        old_selections = {s: v.get() for s, v in self.acc_device_vars.items()}
        
        # Limpiar
        for widget in self.acc_devices_frame.winfo_children():
            widget.destroy()
        self.acc_device_vars.clear()
        if not hasattr(self, 'acc_device_checkboxes'): self.acc_device_checkboxes = {}
        self.acc_device_checkboxes.clear()
        
        if not serials:
            ctk.CTkLabel(self.acc_devices_frame, text="No hay celulares detectados").pack(pady=5)
            return
            
        for serial in serials:
            was_selected = old_selections.get(serial, True)
            var = ctk.BooleanVar(value=was_selected)
            self.acc_device_vars[serial] = var
            cb = ctk.CTkCheckBox(self.acc_devices_frame, text=serial, variable=var)
            self.acc_device_checkboxes[serial] = cb
            cb.pack(pady=2, anchor="w", padx=10)

    def acc_log(self, text, level="info"):
        prefix = "ℹ️"
        if level == "error": prefix = "❌"
        elif level == "warn": prefix = "⚠️"
        elif level == "success": prefix = "✅"
        
        def _do():
            if hasattr(self, 'acc_log_box'):
                self.acc_log_box.insert("end", f"{prefix} {text}\n")
                self.acc_log_box.see("end")
        self.after(0, _do)

    def manual_type_email(self):
        serial = self.account_device_combo.get()
        if not serial or serial == "No hay celulares":
            self.acc_log("Selecciona un celular primero", "warn")
            return
        
        import random
        prefix = self.acc_email_prefix_entry.get().strip()
        domain = self.acc_email_domain_entry.get().strip()
        rnd_num = random.randint(100000, 999999)
        email = f"{prefix}{rnd_num}@{domain}"
        
        self.acc_log(f"Escribiendo correo manual: {email} en {serial}...")
        self.adb.run_command(["shell", "input", "text", email], serial)

    def manual_type_password(self):
        serial = self.account_device_combo.get()
        if not serial or serial == "No hay celulares":
            self.acc_log("Selecciona un celular primero", "warn")
            return
        pwd = self.acc_password_entry.get().strip()
        self.acc_log(f"Escribiendo contraseña manual: {pwd} en {serial}...")
        self.adb.run_command(["shell", "input", "text", pwd], serial)

    def find_and_click_by_text(self, serial, target_texts, do_swipe=False):
        import xml.etree.ElementTree as ET
        import re
        import os
        import time

        for attempt in range(2 if do_swipe else 1):
            self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], serial)
            local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"dump_{serial}.xml")
            
            self.adb.run_command(["pull", "/sdcard/window_dump.xml", local_path], serial)
            if not os.path.exists(local_path):
                continue
            
            try:
                tree = ET.parse(local_path)
                root = tree.getroot()
                os.remove(local_path)
                
                for node in root.iter():
                    text_attr = node.get("text", "")
                    desc_attr = node.get("content-desc", "")
                    
                    match = False
                    for target in target_texts:
                        if target.lower() in text_attr.lower() or target.lower() in desc_attr.lower():
                            match = True
                            break
                            
                    if match:
                        bounds = node.get("bounds", "")
                        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                        if m:
                            x1, y1, x2, y2 = map(int, m.groups())
                            cx = int((x1 + x2) / 2)
                            cy = int((y1 + y2) / 2)
                            self.acc_log(f"Encontrado botón '{text_attr}' en ({cx}, {cy}). Pulsando...")
                            self.adb.run_command(["shell", "input", "tap", str(cx), str(cy)], serial)
                            return True
            except Exception as e:
                self.acc_log(f"Error al analizar pantalla: {str(e)}", "warn")
                if os.path.exists(local_path):
                    os.remove(local_path)
            
            if do_swipe and attempt == 0:
                self.acc_log(f" [{serial}] No se encontró texto. Deslizando hacia abajo...", "info")
                self.adb.run_command(["shell", "input", "swipe", "500", "1500", "500", "500"], serial)
                time.sleep(2)
                
        return False




    def _save_account_memory(self, serial, email, source="Blind"):
        import datetime
        import os
        try:
            filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Cuentas_Creadas.txt")
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(filename, "a", encoding="utf-8") as file:
                file.write(f"[{now}] Dispositivo: {serial} | Correo: {email} | Tipo: {source}\n")
        except Exception as e:
            self.log_msg(f"Error guardando memoria: {e}", "error")



    def _force_portrait(self, serial):
        self.adb.run_command(["shell", "settings", "put", "system", "accelerometer_rotation", "0"], serial)
        self.adb.run_command(["shell", "settings", "put", "system", "user_rotation", "0"], serial)
        # TRUCO SECRETO ANDROID: Forzar refresco de configuración para que gire al instante
        self.adb.run_command(["shell", "am", "broadcast", "-a", "android.intent.action.CONFIGURATION_CHANGED"], serial)


        

    def start_kick_google_login(self):
        if not hasattr(self, 'engine') or not self.engine.active_devices:
            self.acc_log(" [Error] No hay dispositivos activos.", "error")
            return
            
        selected = [dev for dev in self.engine.active_devices if dev['serial'] in self.acc_device_checkboxes and self.acc_device_checkboxes[dev['serial']].get()]
        if not selected:
            selected = self.engine.active_devices
            
        self.acc_log(f" [Kick] Iniciando Pre-Check en {len(selected)} dispositivos...", "info")
        
        # UI Indicator
        if hasattr(self, 'btn_kick_login'):
            self.btn_kick_login.configure(text=" ⏳ Procesando Pre-Check...", fg_color="#F59E0B")
        
        import threading
        threading.Thread(target=self._master_kick_google_login_thread, args=(selected,), daemon=True).start()

    def _master_kick_google_login_thread(self, selected):
        import time
        import xml.etree.ElementTree as ET
        from concurrent.futures import ThreadPoolExecutor
        
        # Read batch size if exists, otherwise 1
        batch_size = 1
        if hasattr(self, 'batch_size_var'):
            val = self.batch_size_var.get()
            if val == "Todos":
                batch_size = len(selected)
            else:
                try: batch_size = int(val)
                except: batch_size = 1

        def check_device(dev):
            s = dev['serial']
            self.acc_log(f" [{s[-4:]}] Verificando sesion actual de Kick...", "info")
            self.adb.run_command(["shell", "am", "force-stop", "com.kick.mobile"], s)
            time.sleep(1)
            self.adb.run_command(["shell", "am", "start", "-n", "com.kick.mobile/com.kick.mobile.MainActivity"], s)
            time.sleep(10)
            
            needs_login = False
            for attempt in range(3):
                root = getattr(self, 'pull_and_parse', lambda x: None)(s)
                if root is None:
                    needs_login = True
                    break
                    
                texts = [n.get("text", "").lower() for n in root.iter("node")]
                
                if any("log in" in t or "iniciar" in t or "inicia" in t or "sign up" in t for t in texts):
                    needs_login = True
                    break
                    
                if any("creadores destacados" in t or "siguiendo" in t for t in texts) and not any("conectándose al chat" in t or "cargando" in t for t in texts):
                    needs_login = False
                    break
                time.sleep(2)
                
            if needs_login:
                self.acc_log(f" [{s[-4:]}] Requiere Login Manual.", "warn")
                if hasattr(self, 'acc_device_checkboxes') and s in self.acc_device_checkboxes:
                    self.after(0, lambda s=s: self.acc_device_checkboxes[s].configure(text=f"{s} ❌", text_color="#EF4444"))
            else:
                self.acc_log(f" [{s[-4:]}] Sesion OK.", "success")
                if hasattr(self, 'acc_device_checkboxes') and s in self.acc_device_checkboxes:
                    self.after(0, lambda s=s: self.acc_device_checkboxes[s].configure(text=f"{s} ✅", text_color="#10B981"))
                    # Desmarcar para que el usuario pueda reintentar solo los que fallaron
                    self.after(0, lambda s=s: self.acc_device_checkboxes[s].deselect())

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            executor.map(check_device, selected)
            
        self.acc_log(" [Kick] Proceso de Verificacion Terminado.", "success")
        if hasattr(self, 'btn_kick_login'):
            self.after(0, lambda: self.btn_kick_login.configure(text=" 1. Pre-Check (Loguear Cuentas)", fg_color="#2563EB"))

    def _kick_google_login_thread(self, serial):
        import time
        import json
        import os
        
        # Cargar memoria de correos
        mem_file = "kick_email_memory.json"
        email_memory = {}
        if os.path.exists(mem_file):
            try:
                with open(mem_file, "r") as mf:
                    email_memory = json.load(mf)
            except: pass
            
        is_slow = getattr(self, "acc_slow_mode_var", None)
        is_slow = is_slow.get() if is_slow else False
        def s_sleep(base_time):
            total = base_time * 2.5 if is_slow else base_time
            time.sleep(total)

        try:
            self.acc_log(f" [{serial[-4:]}] Iniciando Login con Google en KICK...", "info")
            
            self._force_portrait(serial)
            self.acc_log(f" [{serial[-4:]}] Limpiando Kick para Iniciar Sesin...", "warn")
            
            # Orden inteligente: Probar primero el índice que funcionó la vez pasada, luego los demás
            last_working_index = email_memory.get(serial, 0)
            indices_to_try = [last_working_index] + [i for i in range(5) if i != last_working_index]
            
            for email_index in indices_to_try:
                if getattr(self, 'stop_signup', False): break
                
                self.adb.run_command(["shell", "am", "force-stop", "com.kick.mobile"], serial)
                self.adb.run_command(["shell", "pm", "clear", "com.kick.mobile"], serial)
                s_sleep(2)
                self.adb.run_command(["shell", "am", "start", "-n", "com.kick.mobile/com.kick.mobile.MainActivity"], serial)
                
                self.acc_log(f" [{serial[-4:]}] Esperando 20 segundos a que Kick cargue...", "info")
                s_sleep(20) # 20 SEGUNDOS COMO PIDIO EL USUARIO
                
                # Iniciar Sesion (Barra superior)
                click_login = self.find_and_click_by_text(serial, ["iniciar sesi", "log in"], do_swipe=False)
                if not click_login:
                    self.acc_log(f" [{serial[-4:]}] ❌ No se encontro boton 'Iniciar sesion'. Reintentando...", "error")
                    continue # No hacemos toque ciego para evitar ir a la Play Store
                    
                s_sleep(8)
                
                # --- NUEVO: Ocultar teclado si aparece ---
                # Kick enfoca automticamente el campo de texto y saca el teclado, tapando el botn de Google.
                try:
                    stdout, _, _ = self.adb.run_command(["shell", "dumpsys", "input_method"], serial)
                    if "mInputShown=true" in stdout:
                        self.acc_log(f" [{serial[-4:]}] Teclado detectado tapando la pantalla. Ocultando...", "info")
                        self.adb.run_command(["shell", "input", "keyevent", "4"], serial)
                        time.sleep(2)
                except Exception as e:
                    self.acc_log(f" [{serial[-4:]}] Error checkeando teclado: {e}", "error")
                # ---------------------------------------
                
                # Continuar con Google
                click_google = self.find_and_click_by_text(serial, ["continuar con google", "continue with google", "google"], do_swipe=False)
                if not click_google:
                    self.acc_log(f" [{serial[-4:]}] ❌ No se encontro boton 'Google'. Reintentando...", "error")
                    continue
                    
                s_sleep(12)
                
                # Seleccionar cuenta Gmail por índice
                # Hacemos tap directo porque buscar texto siempre le da clic al primer correo de la lista.
                self.acc_log(f" [{serial[-4:]}] Seleccionando correo en el índice {email_index}...", "info")
                y_offset = 310 + (email_index * 80)
                self.adb.run_command(["shell", "input", "tap", "240", str(y_offset)], serial)
                
                self.acc_log(f" [{serial[-4:]}] Esperando 40s a que procese el inicio de sesión...", "info")
                s_sleep(40) # Aumentado a 40s porque Kick demora mucho en autenticar el correo
                
                # Omitir pantalla de Onboarding ("Cuéntanos un poco sobre ti" -> "Tal vez después")
                click_onboarding = self.find_and_click_by_text(serial, ["tal vez despu", "maybe later", "omitir", "skip"], do_swipe=False)
                if click_onboarding:
                    self.acc_log(f" [{serial[-4:]}] Pantalla de bienvenida saltada ('Tal vez después')...", "info")
                    s_sleep(5)
                
                # VERIFICACION FINAL (Segundo check)
                self.acc_log(f" [{serial[-4:]}] Realizando segundo check para confirmar inicio de sesion...", "info")
                root2 = getattr(self, 'pull_and_parse', lambda x: None)(serial)
                if root2 is not None:
                    texts2 = [n.get("text", "").lower() for n in root2.iter("node")]
                    if any("creadores destacados" in t or "tu cuenta" in t or "siguiendo" in t or "explorar" in t for t in texts2) and not any("log in" in t or "iniciar sesi" in t for t in texts2):
                        self.acc_log(f" [{serial[-4:]}] ✅ KICK CONFIRMADO LOGUEADO CON EXITO.", "success")
                        
                        # Guardar en memoria
                        email_memory[serial] = email_index
                        try:
                            with open(mem_file, "w") as mf:
                                json.dump(email_memory, mf)
                        except: pass
                        
                        if hasattr(self, 'acc_device_checkboxes') and serial in self.acc_device_checkboxes:
                            self.after(0, lambda s=serial: self.acc_device_checkboxes[s].configure(text=f"{s} ✅", text_color="#10B981"))
                        return True
                    else:
                        self.acc_log(f" [{serial[-4:]}] ⚠️ Falló la verificación de sesión. Intentando otro correo...", "warn")
                        
            self.acc_log(f" [{serial[-4:]}] ❌ Fallo Login en Kick tras 5 intentos.", "error")
            return False
            
        except Exception as e:
            self.acc_log(f" [{serial[-4:]}] Error en Kick Login: {e}", "error")
            return False






    def pull_and_parse(self, serial):
        import xml.etree.ElementTree as ET
        self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/dump.xml"], serial)
        self.adb.run_command(["pull", "/sdcard/dump.xml", "dump.xml"], serial)
        try:
            with open("dump.xml", "r", encoding="utf-8", errors="ignore") as f:
                return ET.fromstring(f.read())
        except:
            return None











if __name__ == "__main__":
    try:
        debug_log("Entrando a Main Loop")
        app = MarketingeoApp()
        app.mainloop()
    except Exception as e:
        err = f"ERROR CRITICO EN ARRANQUE: {str(e)}"
        print(err)
        debug_log(err)
        speak("Se ha detectado un error critico. Revisa el archivo de registro.")
        with open("CRASH_REPORT.txt", "w") as f:
            traceback.print_exc(file=f)
