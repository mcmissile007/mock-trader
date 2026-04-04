# Antigravity AI Agent

Este repositorio utiliza **Antigravity** como agente asistente principal de IA. A diferencia de otras herramientas que dependen de un extenso y único archivo de configuración (como por ejemplo `CLAUDE.md`), Antigravity mantiene el contexto utilizando un diseño modular en carpetas y un sistema de memoria (KIs) local fuera del propio repositorio.

Este archivo tiene propósitos de documentación para que todos los miembros del equipo que utilicen otras herramientas comprendan cómo el Agente interactúa con este proyecto.

## 📂 Estructura de Entorno

Toda la automatización e instrucciones específicas se alojan en el directorio oculto `.agent/` de la raíz del proyecto.

### 1. Flujos de Trabajo / Workflows (`.agent/workflows/`)
Contiene recetas paso a paso que actúan como "slash commands" para el agente (ej. `/comando`). Almacena procesos que frecuentemente incluirías en la sección *build* o *test* de un `CLAUDE.md`.

**Workflows configurados actualmente**:
- `/quality-check`: Verifica linters y convenciones (`.agent/workflows/quality-check.md`)
- `/contribution`: Guía la creación de una contribución estándar para Mock Trader (`.agent/workflows/contribution.md`)

*(Para agregar un nuevo comando, los miembros del equipo solo deben crear un archivo Markdown nuevo en este directorio listando los pasos o comandos que el agente debe correr).*

### 2. Reglas y Contexto (`.agent/rules/` & `.agent/skills/`)
Desglosa el contexto arquitectónico o de prácticas limpias que en otras herramientas estarían apretados en un único documento de texto. Se leen automáticamente:

**Reglas actuales**:
- `ARCHITECTURE.md`: Directrices y filosofía de arquitectura del Mock Trader.
- `CODE.md`: Prácticas de código, estilo, librerías aceptadas.

### 3. Knowledge Items (KIs) - Sistema de Memoria Autónoma
Antigravity genera automáticamente su propia "memoria del repositorio" y la archiva localmente fuera del entorno del código fuente. Opera en dos capas de memoria:

1.  **Conversation Logs (Memoria Cruda)**: Todos los pasos, archivos tocados y detalles de ejecución se almacenan en el historial local de chats en `~/.gemini/antigravity/brain/`.
2.  **KIs (Conocimiento Curado)**: Cuando el agente detecta un problema persistente, una peculiaridad arquitectónica (un "gotcha") o convenciones críticas surgidas en las discusiones, las destila y las compila como Knowledge Items en la carpeta `~/.gemini/antigravity/knowledge/`. Cada vez que Antigravity abre el proyecto, escanea este conocimiento.

**Nota**: Es completamente normal que la carpeta de KIs esté vacía al comenzar o cuando todos los patrones ya están estipulados correctamente en la carpeta `.agent/rules/`. El agente solo genera esta información destilada bajo demanda para optimizar el contexto a largo plazo (evitando saturar el espacio con datos irrelevantes).

---
> [!IMPORTANT]
> **Aviso para el equipo**: Por favor, no empleen este archivo (`ANTIGRAVITY.md`) con la intención de agregar prompts generales o directivas para el Agente. Si el equipo precisa establecer nuevas metodologías, generen un archivo particular en `.agent/rules/` (ej. `TESTING.md`) o un comando estructurado dentro de `.agent/workflows/` para mantener la modularidad y limpieza del proyecto.
