"""
models.py — Modelo de dominio del sistema de biblioteca.

Define la entidad Libro como dataclass con validación de campos.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# Patrón ISBN-13: exactamente 13 dígitos (sin guiones)
_ISBN_PATTERN = re.compile(r"^\d{13}$")


def validar_isbn(isbn: str) -> bool:
    """Verifica que un ISBN tenga formato válido (13 dígitos numéricos).

    Args:
        isbn: Cadena a validar como ISBN-13.

    Returns:
        True si el ISBN tiene exactamente 13 dígitos, False en caso contrario.
    """
    return bool(_ISBN_PATTERN.match(isbn.strip()))


@dataclass
class Libro:
    """Representa un libro en la biblioteca.

    Attributes:
        isbn: Código ISBN-13 del libro (13 dígitos).
        titulo: Título completo del libro.
        autor: Nombre del autor.
        total: Cantidad total de ejemplares en la biblioteca.
        prestados: Cantidad de ejemplares actualmente prestados.
    """

    isbn: str
    titulo: str
    autor: str
    total: int
    prestados: int

    @property
    def disponibles(self) -> int:
        """Calcula los ejemplares disponibles para préstamo."""
        return self.total - self.prestados

    def __post_init__(self) -> None:
        """Valida la coherencia de los datos al crear un Libro."""
        if self.total < 0:
            raise ValueError(f"El total de ejemplares no puede ser negativo: {self.total}")
        if self.prestados < 0:
            raise ValueError(f"Los ejemplares prestados no pueden ser negativos: {self.prestados}")
        if self.prestados > self.total:
            raise ValueError(
                f"Los prestados ({self.prestados}) no pueden superar el total ({self.total})"
            )
