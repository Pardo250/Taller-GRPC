from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import threading

@dataclass
class Libro:
    isbn: str
    titulo: str
    autor: str
    total: int
    prestados: int

    @property
    def disponibles(self) -> int:
        return self.total - self.prestados


class RepositorioTxtBiblioteca:
    """
    BD en TXT:
    ISBN|TITULO|AUTOR|TOTAL|PRESTADOS
    """
    def __init__(self, ruta_archivo: str):
        self.path = Path(ruta_archivo)
        self._lock = threading.Lock()

    def _ensure_file(self) -> None:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("", encoding="utf-8")

    def cargar(self) -> List[Libro]:
        self._ensure_file()
        libros: List[Libro] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            if len(parts) != 5:
                continue
            isbn, titulo, autor, total, prestados = [p.strip() for p in parts]
            libros.append(
                Libro(
                    isbn=isbn,
                    titulo=titulo,
                    autor=autor,
                    total=int(total),
                    prestados=int(prestados),
                )
            )
        return libros

    def guardar(self, libros: List[Libro]) -> None:
        self._ensure_file()
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        contenido = "\n".join(
            f"{l.isbn}|{l.titulo}|{l.autor}|{l.total}|{l.prestados}" for l in libros
        ) + ("\n" if libros else "")
        tmp.write_text(contenido, encoding="utf-8")
        tmp.replace(self.path)

    def buscar_por_isbn(self, libros: List[Libro], isbn: str) -> Optional[Libro]:
        isbn = isbn.strip().lower()
        for l in libros:
            if l.isbn.lower() == isbn:
                return l
        return None

    def buscar_por_titulo(self, libros: List[Libro], titulo: str) -> Optional[Libro]:
        t = titulo.strip().lower()
        for l in libros:
            if l.titulo.strip().lower() == t:
                return l
        return None

    # Operaciones atómicas (con lock)
    def with_lock(self):
        return self._lock
