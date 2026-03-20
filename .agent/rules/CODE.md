---
description: Project coding rules and conventions
---

# Reglas del Proyecto

Directrices para el desarrollo de software en Mock Trader.

## 1. Idioma
*   **Código**: Inglés. Variables, funciones, clases y módulos en inglés.
*   **Comentarios**: Inglés.
*   **Git Commits**: Inglés, siguiendo Conventional Commits.

## 2. Naming Conventions (Python)
*   **Variables y Funciones**: `snake_case`.
*   **Clases**: `PascalCase`.
*   **Constantes**: `SCREAMING_SNAKE_CASE`.

## 3. Tipado (Type Hints)
*   **Nivel**: Estricto.
*   **Requisito**: Todas las funciones y métodos deben tener anotaciones de tipo.
    ```python
    def process_data(data: dict[str, Any]) -> list[str]:
        ...
    ```

## 4. Documentación
*   **Estilo**: Google Style Docstrings.
*   **Requisito**: Todas las funciones, clases y métodos públicos documentados.

## 5. Formato y Estilo
*   **Longitud de Línea**: 88 caracteres.
*   **Comillas**: Dobles (`"`).
*   **Imports**: Organizados (stdlib, third-party, local).

## 6. Manejo de Errores
*   **EAFP** (`try/except`) para I/O, DB y operaciones externas.
*   **LBYL** (`if check:`) para lógica de negocio y validaciones.

## 7. Diseño de Código
*   **Principio**: KISS.
*   Escribe código simple primero. Abstracciones solo cuando se repita 3+ veces.

## 8. Resiliencia
*   El sistema puede pararse y reiniciarse en cualquier momento.
*   Estado siempre en PostgreSQL — nunca en memoria persistente.
*   Manejar errores de red (Binance API) con logging y retry.
