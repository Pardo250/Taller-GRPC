"""
repo_txt.py — Capa de persistencia basada en archivo de texto plano.

Implementa el patrón Repository para gestionar la lectura y escritura
de libros en un archivo con formato pipe-separated (|).

Formato de cada línea:
    ISBN|TITULO|AUTOR|TOTAL|PRESTADOS
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import List, Optional

from models import Libro, validar_isbn

logger = logging.getLogger(__name__)


class RepositorioTxtBiblioteca:
    """Repositorio que persiste libros en un archivo de texto plano.

    Cada línea del archivo representa un libro con campos separados
    por el carácter pipe (|). Proporciona operaciones de lectura,
    escritura y búsqueda con soporte de concurrencia mediante Lock.

    Attributes:
        path: Ruta al archivo de datos.
    """

    def __init__(self, ruta_archivo: str) -> None:
        """Inicializa el repositorio con la ruta al archivo de datos.

        Args:
            ruta_archivo: Ruta relativa o absoluta al archivo TXT de la biblioteca.
        """
        self.path = Path(ruta_archivo)
        self._lock = threading.Lock()
        logger.info("Repositorio inicializado con archivo: %s", self.path.resolve())

    def _ensure_file(self) -> None:
        """Crea el archivo y sus directorios padre si no existen."""
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("", encoding="utf-8")
            logger.info("Archivo de datos creado: %s", self.path)

    def cargar(self) -> List[Libro]:
        """Lee todos los libros del archivo de datos.

        Ignora líneas vacías y líneas con formato incorrecto (≠ 5 campos).
        Registra advertencias para líneas malformadas.

        Returns:
            Lista de objetos Libro con los datos cargados del archivo.
        """
        self._ensure_file()
        libros: List[Libro] = []
        for numero_linea, linea in enumerate(
            self.path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            linea = linea.strip()
            if not linea:
                continue
            partes = linea.split("|")
            if len(partes) != 5:
                logger.warning("Línea %d ignorada (formato inválido): %s", numero_linea, linea)
                continue
            isbn, titulo, autor, total_str, prestados_str = [p.strip() for p in partes]
            try:
                libros.append(
                    Libro(
                        isbn=isbn,
                        titulo=titulo,
                        autor=autor,
                        total=int(total_str),
                        prestados=int(prestados_str),
                    )
                )
            except (ValueError, TypeError) as error:
                logger.warning("Línea %d ignorada (datos inválidos): %s — %s", numero_linea, linea, error)
        return libros

    def guardar(self, libros: List[Libro]) -> None:
        """Escribe todos los libros al archivo de datos de forma atómica.

        Utiliza un archivo temporal intermedio para garantizar que la
        escritura sea atómica y no corrompa los datos existentes.

        Args:
            libros: Lista de libros a persistir.
        """
        self._ensure_file()
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        contenido = "\n".join(
            f"{libro.isbn}|{libro.titulo}|{libro.autor}|{libro.total}|{libro.prestados}"
            for libro in libros
        ) + ("\n" if libros else "")
        tmp.write_text(contenido, encoding="utf-8")
        tmp.replace(self.path)
        logger.debug("Archivo de datos guardado con %d registros.", len(libros))

    def buscar_por_isbn(self, libros: List[Libro], isbn: str) -> Optional[Libro]:
        """Busca un libro por su ISBN (comparación case-insensitive).

        Args:
            libros: Lista de libros donde buscar.
            isbn: ISBN a buscar.

        Returns:
            El Libro encontrado o None si no existe.
        """
        isbn_normalizado = isbn.strip().lower()
        for libro in libros:
            if libro.isbn.lower() == isbn_normalizado:
                return libro
        return None

    def buscar_por_titulo(self, libros: List[Libro], titulo: str) -> Optional[Libro]:
        """Busca un libro por su título exacto (comparación case-insensitive).

        Args:
            libros: Lista de libros donde buscar.
            titulo: Título a buscar.

        Returns:
            El Libro encontrado o None si no existe.
        """
        titulo_normalizado = titulo.strip().lower()
        for libro in libros:
            if libro.titulo.strip().lower() == titulo_normalizado:
                return libro
        return None

    def with_lock(self) -> threading.Lock:
        """Retorna el lock interno para operaciones atómicas.

        Uso:
            with repo.with_lock():
                # operaciones protegidas
        """
        return self._lock
