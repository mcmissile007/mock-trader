---
description: Verificación de calidad local (lint + format)
---

Ejecuta las comprobaciones de calidad antes de hacer push.

// turbo-all

1. **Lint (Ruff check)**:
   ```bash
   cd /home/falken/code/mock-trader && ruff check src/ scripts/ tests/
   ```

2. **Format (Ruff format)**:
   ```bash
   cd /home/falken/code/mock-trader && ruff format --check src/ scripts/ tests/
   ```

3. **Resultado**:
   - Si todo pasa, informa al usuario que el código está listo para push.
   - Si algo falla, muestra qué falló y sugiere cómo arreglarlo.
