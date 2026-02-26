"""
test_repo.py — Tests unitarios para models.py y repo_txt.py.

Ejecutar con:
    python -m pytest test_repo.py -v
"""

import os
import tempfile
from pathlib import Path

import pytest

from models import Libro, validar_isbn
from repo_txt import RepositorioTxtBiblioteca


# ── Tests de Modelo ─────────────────────────────────────────────


class TestLibro:
    """Tests para la dataclass Libro."""

    def test_disponibles_se_calcula_correctamente(self):
        libro = Libro(isbn="1234567890123", titulo="Test", autor="Autor", total=5, prestados=2)
        assert libro.disponibles == 3

    def test_disponibles_todos_prestados(self):
        libro = Libro(isbn="1234567890123", titulo="Test", autor="Autor", total=3, prestados=3)
        assert libro.disponibles == 0

    def test_validacion_prestados_mayor_que_total(self):
        with pytest.raises(ValueError, match="no pueden superar el total"):
            Libro(isbn="1234567890123", titulo="Test", autor="Autor", total=2, prestados=5)

    def test_validacion_total_negativo(self):
        with pytest.raises(ValueError, match="no puede ser negativo"):
            Libro(isbn="1234567890123", titulo="Test", autor="Autor", total=-1, prestados=0)

    def test_validacion_prestados_negativo(self):
        with pytest.raises(ValueError, match="no pueden ser negativos"):
            Libro(isbn="1234567890123", titulo="Test", autor="Autor", total=5, prestados=-1)


class TestValidarIsbn:
    """Tests para la función validar_isbn."""

    def test_isbn_valido_13_digitos(self):
        assert validar_isbn("9780134685991") is True

    def test_isbn_invalido_corto(self):
        assert validar_isbn("12345") is False

    def test_isbn_invalido_con_letras(self):
        assert validar_isbn("978013468A991") is False

    def test_isbn_vacio(self):
        assert validar_isbn("") is False

    def test_isbn_con_espacios(self):
        assert validar_isbn("  9780134685991  ") is True


# ── Tests de Repositorio ────────────────────────────────────────


@pytest.fixture
def repo_temporal():
    """Crea un repositorio con archivo temporal para tests."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("9780134685991|Effective Java|Joshua Bloch|5|2\n")
        f.write("9781492078005|Designing Data-Intensive Applications|Martin Kleppmann|3|0\n")
        f.write("9780132350884|Clean Code|Robert C. Martin|4|4\n")
        ruta = f.name
    repo = RepositorioTxtBiblioteca(ruta)
    yield repo
    os.unlink(ruta)


class TestRepositorio:
    """Tests para RepositorioTxtBiblioteca."""

    def test_cargar_libros(self, repo_temporal):
        libros = repo_temporal.cargar()
        assert len(libros) == 3

    def test_cargar_primer_libro(self, repo_temporal):
        libros = repo_temporal.cargar()
        assert libros[0].isbn == "9780134685991"
        assert libros[0].titulo == "Effective Java"
        assert libros[0].autor == "Joshua Bloch"
        assert libros[0].total == 5
        assert libros[0].prestados == 2

    def test_buscar_por_isbn_existente(self, repo_temporal):
        libros = repo_temporal.cargar()
        libro = repo_temporal.buscar_por_isbn(libros, "9780134685991")
        assert libro is not None
        assert libro.titulo == "Effective Java"

    def test_buscar_por_isbn_case_insensitive(self, repo_temporal):
        libros = repo_temporal.cargar()
        libro = repo_temporal.buscar_por_isbn(libros, "9780134685991")
        assert libro is not None

    def test_buscar_por_isbn_inexistente(self, repo_temporal):
        libros = repo_temporal.cargar()
        libro = repo_temporal.buscar_por_isbn(libros, "0000000000000")
        assert libro is None

    def test_buscar_por_titulo_existente(self, repo_temporal):
        libros = repo_temporal.cargar()
        libro = repo_temporal.buscar_por_titulo(libros, "Clean Code")
        assert libro is not None
        assert libro.isbn == "9780132350884"

    def test_buscar_por_titulo_case_insensitive(self, repo_temporal):
        libros = repo_temporal.cargar()
        libro = repo_temporal.buscar_por_titulo(libros, "clean code")
        assert libro is not None

    def test_buscar_por_titulo_inexistente(self, repo_temporal):
        libros = repo_temporal.cargar()
        libro = repo_temporal.buscar_por_titulo(libros, "Libro Inexistente")
        assert libro is None

    def test_guardar_y_recargar(self, repo_temporal):
        libros = repo_temporal.cargar()
        libros[0].prestados += 1
        repo_temporal.guardar(libros)

        libros_recargados = repo_temporal.cargar()
        assert libros_recargados[0].prestados == 3

    def test_cargar_lineas_malformadas(self):
        """Las líneas con formato incorrecto se ignoran sin error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("9780134685991|Effective Java|Joshua Bloch|5|2\n")
            f.write("linea_malformada\n")
            f.write("\n")
            f.write("9781492078005|Designing Data|Martin|3|0\n")
            ruta = f.name
        repo = RepositorioTxtBiblioteca(ruta)
        libros = repo.cargar()
        assert len(libros) == 2
        os.unlink(ruta)

    def test_archivo_inexistente_se_crea(self):
        """Si el archivo no existe, se crea automáticamente."""
        ruta = os.path.join(tempfile.gettempdir(), "test_biblioteca_nueva.txt")
        if os.path.exists(ruta):
            os.unlink(ruta)
        repo = RepositorioTxtBiblioteca(ruta)
        libros = repo.cargar()
        assert libros == []
        assert os.path.exists(ruta)
        os.unlink(ruta)

    def test_prestamo_y_devolucion_flujo(self, repo_temporal):
        """Simula un flujo completo de préstamo y devolución."""
        libros = repo_temporal.cargar()
        libro = repo_temporal.buscar_por_isbn(libros, "9780134685991")
        disponibles_antes = libro.disponibles  # 3

        # Préstamo
        libro.prestados += 1
        repo_temporal.guardar(libros)

        libros = repo_temporal.cargar()
        libro = repo_temporal.buscar_por_isbn(libros, "9780134685991")
        assert libro.disponibles == disponibles_antes - 1

        # Devolución
        libro.prestados -= 1
        repo_temporal.guardar(libros)

        libros = repo_temporal.cargar()
        libro = repo_temporal.buscar_por_isbn(libros, "9780134685991")
        assert libro.disponibles == disponibles_antes

    def test_lock_se_puede_adquirir(self, repo_temporal):
        """Verifica que el lock funciona correctamente."""
        with repo_temporal.with_lock():
            libros = repo_temporal.cargar()
            assert len(libros) > 0
