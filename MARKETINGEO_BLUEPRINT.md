# Blueprint de Arquitectura: Marketingeo Bot Farm

Este documento establece las reglas de diseño, interfaz, y seguridad de la aplicación **Marketingeo**. Debe usarse como **"Prompt de Contexto"** o **Guía Maestra** cada vez que se desee desarrollar un nuevo módulo (ej. TikTok, Facebook, Instagram) para garantizar que el sistema sea orgánico, no sufra colisiones (crashes), y mantenga una interfaz profesional.

---

## 1. Reglas de Interfaz de Usuario (UI/UX)
El sistema utiliza `customtkinter`. Las reglas de diseño son estrictas para mantener la consistencia:

* **Estados de Botones (Feedback Visual):**
  * **[VERDE / AZUL] (Estado Normal):** El botón está listo para usarse.
  * **[NARANJA / AMARILLO] (Estado Activo):** El botón está ejecutando un proceso en segundo plano (Ej: `"Inyectando..."` o `"Cascada Activa"`).
  * **[ROJO] (Botones de Aborto):** Botones de parada de emergencia.
* **Información Integrada:** Cualquier módulo complejo debe incluir botones grises pequeños de `[ℹ️ Ayuda / Info]` que desplieguen un Modal (`CTkToplevel`) explicando el uso y advertencias de esa sección.
* **Tarjetas de Dispositivo:** El panel de control debe tener tarjetas por cada celular conectado. Cada tarjeta debe ser independiente y mostrar: IP, Estado, Botón de Pausa (`⏸️ / ▶️`), y su Personalidad (IA).

---

## 2. Directrices Anti-Choque (Safety Locks)
Como todos los procesos operan físicamente la pantalla de los celulares mediante ADB, **chocarán** si dos hilos intentan controlar el mismo teléfono.

* **Bloqueo de Interfaz Mutuamente Excluyente:**
  * Si un Bot cíclico (Ej. Cascada) se inicia, se deben usar `.configure(state="disabled")` en todos los demás botones de inyección, login o escaneo.
  * Al detener el bot, se deben devolver a `.configure(state="normal")`.
* **Cancelación Inmediata (Freno de Emergencia):**
  * No usar `time.sleep(20)` de golpe. Si un proceso necesita esperar, usar un bucle fragmentado que escuche el estado de aborto general para poder cancelar en el aire:
    ```python
    for _ in range(20):
        if getattr(self, "stop_social_threads", False): return
        time.sleep(1)
    ```

---

## 3. Motor de Inteligencia Artificial (Simulador Orgánico)
Las plataformas (Kick, TikTok, IG) banean granjas si detectan patrones robóticos. Nunca crear secuencias rígidas (Ej: Comentar -> Esperar -> Emoji -> Repetir).

* **El Principio del "Dado Virtual":** 
  En cada lote, cada dispositivo debe tirar un número aleatorio del 1 al 100 para decidir su acción basándose en su "Personalidad":
  * *Fanático:* Comenta y da likes sin parar.
  * *Fantasma:* Solo mira la pantalla, simulando "Lurking" dando doble taps para evitar que la pantalla se apague.
  * *Spammer:* Solo lanza Emojis.
* **Control de Pausa Individual:** El motor IA debe verificar si un dispositivo en particular está "Pausado" (`self.device_ai_states[serial]["paused"]`). Si lo está, el loop general simplemente lo ignora y pasa al siguiente, sin detener toda la granja.

---

## 4. El "Guardián" (Auto-Healing)
Ningún bot debe ejecutar clics a ciegas asumiendo que la App está abierta.
* **Regla del Guardián:** Antes de que el Bot comente o mande un like, debe hacer un chequeo de qué aplicación está en pantalla (`dumpsys window windows`).
* **Auto-Reparación:** Si la app objetivo se cerró o crasheó, el Guardián debe reinyectar el enlace de Deep Link (Ej: `am start -a android.intent.action.VIEW -d "url"`), esperar a que cargue, y luego continuar su trabajo.

---

## 5. Plantilla de Desarrollo para Nuevos Módulos (TikTok, Facebook, etc.)
Cuando pidas crear un nuevo módulo a la IA, entrégale este documento e indícale que estructure el nuevo código en estas 3 fases:

1. **Fase de Inyección (Deep Linking):** ¿Cómo inyectaremos al celular directo al post o live usando comandos ADB Intent?
2. **Fase de Extracción de Coordenadas (UIAutomator / Fallbacks):** Identificar las proporciones de los botones de Like, Comentar y Swipe (Ej: `height * 0.85` para la caja de chat).
3. **Fase de Motor IA:** Diseñar qué opciones aleatorias puede tomar un humano en esa red social específica (Ej. En TikTok: Hacer Swipe arriba, Compartir, Dar tap repetido al corazón, o Escribir texto).
