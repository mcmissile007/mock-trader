---
description: Workflow estándar para crear una contribución en Mock Trader
---

Sigue estos pasos para cualquier cambio en el código:

1.  **Entender la Tarea**: Analiza qué hay que hacer.
    - Si es complejo, crea/actualiza `implementation_plan.md`.

2.  **Implementar Cambios**:
    - Realiza los cambios necesarios.
    - **IMPORTANTE**: Si añades funcionalidad o cambias configuración, actualiza `README.md`.

3.  **Actualizar Documentación**:
    - Si se toma una decisión de diseño → añadir entrada `DD-XXX` en `SPEC.md`.
    - Si cambia el estado de una fase → actualizar tabla en `SPEC.md` § Pipeline Status.
    - Si cambia la estructura → actualizar `.agent/rules/ARCHITECTURE.md`.

4.  **Verificar (Quality Check)**:
    - Ejecuta SIEMPRE antes de commitear.
    // turbo
    ```bash
    cd /path/to/mock-trader && ruff check *.py && ruff format --check *.py
    ```
    - Si fallan, corrige y repite.

5.  **Commit y Push**:
    - Usa Conventional Commits: `tipo(alcance): descripción`.
    - Ej: `feat(trader): add LLM trader`, `fix(monitor): handle API timeout`.
    - Push directo a main: `git push origin main`.
