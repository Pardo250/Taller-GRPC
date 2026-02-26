"""
server.py — Servidor gRPC del sistema de gestión de biblioteca.

Inicia un servidor gRPC con ThreadPoolExecutor que expone el servicio
BibliotecaService para operaciones de consulta, préstamo y devolución
de libros.
"""

from concurrent import futures
from datetime import date, timedelta
import logging

import grpc

import biblioteca_pb2 as pb2
import biblioteca_pb2_grpc as pb2_grpc
from models import validar_isbn
from repo_txt import RepositorioTxtBiblioteca

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


class BibliotecaService(pb2_grpc.BibliotecaServiceServicer):
    """Implementación del servicio gRPC para gestión de biblioteca.

    Ofrece operaciones de consulta, préstamo (por ISBN o título)
    y devolución de libros. Todas las operaciones de escritura
    están protegidas con lock para garantizar thread-safety.

    Attributes:
        repo: Repositorio de datos de la biblioteca.
    """

    def __init__(self, repo: RepositorioTxtBiblioteca) -> None:
        """Inicializa el servicio con el repositorio de datos.

        Args:
            repo: Instancia de RepositorioTxtBiblioteca para persistencia.
        """
        self.repo = repo

    # ── Consulta ────────────────────────────────────────────────

    def ConsultarPorIsbn(self, request: pb2.ConsultaRequest, context) -> pb2.ConsultaResponse:
        """Consulta la información de un libro dado su ISBN.

        Busca el libro en la base de datos y retorna sus datos
        completos incluyendo disponibilidad. La lectura se realiza
        bajo lock para evitar lecturas inconsistentes.

        Args:
            request: Mensaje con el ISBN a consultar.
            context: Contexto gRPC de la llamada.

        Returns:
            ConsultaResponse con la información del libro o mensaje de error.
        """
        isbn = request.isbn.strip()
        if not isbn:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("El ISBN no puede estar vacío.")
            return pb2.ConsultaResponse(existe=False, mensaje="El ISBN no puede estar vacío.")

        with self.repo.with_lock():
            try:
                libros = self.repo.cargar()
                libro = self.repo.buscar_por_isbn(libros, isbn)
                if not libro:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(f"No existe un libro con ISBN: {isbn}")
                    return pb2.ConsultaResponse(existe=False, mensaje="No existe un libro con ese ISBN.")
                logger.info("Consulta exitosa — ISBN: %s, Título: %s", libro.isbn, libro.titulo)
                return pb2.ConsultaResponse(
                    existe=True,
                    mensaje="Libro encontrado.",
                    isbn=libro.isbn,
                    titulo=libro.titulo,
                    autor=libro.autor,
                    total=libro.total,
                    prestados=libro.prestados,
                    disponibles=libro.disponibles,
                )
            except Exception as error:
                logger.exception("Error al consultar ISBN %s", isbn)
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(str(error))
                return pb2.ConsultaResponse(existe=False, mensaje=f"Error consultando: {error}")

    # ── Préstamos ───────────────────────────────────────────────

    def _realizar_prestamo(self, libro, libros, context) -> pb2.PrestamoResponse:
        """Lógica común para realizar un préstamo de libro.

        Verifica disponibilidad, incrementa el contador de préstamos,
        persiste los cambios y calcula la fecha de devolución.

        Args:
            libro: Instancia de Libro a prestar (ya validada como existente).
            libros: Lista completa de libros (para persistir).
            context: Contexto gRPC de la llamada.

        Returns:
            PrestamoResponse indicando éxito o fallo del préstamo.
        """
        if libro.disponibles <= 0:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details(f"No hay ejemplares disponibles de '{libro.titulo}'.")
            return pb2.PrestamoResponse(ok=False, mensaje="No hay ejemplares disponibles.")

        libro.prestados += 1
        self.repo.guardar(libros)

        fecha_devolucion = (date.today() + timedelta(days=7)).isoformat()
        logger.info(
            "Préstamo realizado — ISBN: %s, Título: %s, Disponibles: %d",
            libro.isbn, libro.titulo, libro.disponibles,
        )
        return pb2.PrestamoResponse(
            ok=True,
            mensaje="Préstamo realizado.",
            fecha_devolucion=fecha_devolucion,
            disponibles_restantes=libro.disponibles,
        )

    def PrestarPorIsbn(self, request: pb2.PrestamoIsbnRequest, context) -> pb2.PrestamoResponse:
        """Registra el préstamo de un libro dado su ISBN.

        Busca el libro por ISBN, verifica disponibilidad y registra
        el préstamo con fecha de devolución a 7 días.

        Args:
            request: Mensaje con el ISBN del libro a prestar.
            context: Contexto gRPC de la llamada.

        Returns:
            PrestamoResponse con resultado del préstamo y fecha de devolución.
        """
        isbn = request.isbn.strip()
        if not isbn:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("El ISBN no puede estar vacío.")
            return pb2.PrestamoResponse(ok=False, mensaje="El ISBN no puede estar vacío.")

        with self.repo.with_lock():
            try:
                libros = self.repo.cargar()
                libro = self.repo.buscar_por_isbn(libros, isbn)
                if not libro:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(f"No existe un libro con ISBN: {isbn}")
                    return pb2.PrestamoResponse(ok=False, mensaje="No existe un libro con ese ISBN.")
                return self._realizar_prestamo(libro, libros, context)
            except Exception as error:
                logger.exception("Error al prestar por ISBN %s", isbn)
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(str(error))
                return pb2.PrestamoResponse(ok=False, mensaje=f"Error prestando: {error}")

    def PrestarPorTitulo(self, request: pb2.PrestamoTituloRequest, context) -> pb2.PrestamoResponse:
        """Registra el préstamo de un libro dado su título exacto.

        Busca el libro por título (case-insensitive), verifica
        disponibilidad y registra el préstamo con fecha de devolución a 7 días.

        Args:
            request: Mensaje con el título del libro a prestar.
            context: Contexto gRPC de la llamada.

        Returns:
            PrestamoResponse con resultado del préstamo y fecha de devolución.
        """
        titulo = request.titulo.strip()
        if not titulo:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("El título no puede estar vacío.")
            return pb2.PrestamoResponse(ok=False, mensaje="El título no puede estar vacío.")

        with self.repo.with_lock():
            try:
                libros = self.repo.cargar()
                libro = self.repo.buscar_por_titulo(libros, titulo)
                if not libro:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(f"No existe un libro con título: {titulo}")
                    return pb2.PrestamoResponse(ok=False, mensaje="No existe un libro con ese título.")
                return self._realizar_prestamo(libro, libros, context)
            except Exception as error:
                logger.exception("Error al prestar por título '%s'", titulo)
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(str(error))
                return pb2.PrestamoResponse(ok=False, mensaje=f"Error prestando: {error}")

    # ── Devolución ──────────────────────────────────────────────

    def DevolverPorIsbn(self, request: pb2.DevolucionRequest, context) -> pb2.DevolucionResponse:
        """Registra la devolución de un libro dado su ISBN.

        Busca el libro por ISBN, verifica que existan préstamos pendientes
        y decrementa el contador de préstamos.

        Args:
            request: Mensaje con el ISBN del libro a devolver.
            context: Contexto gRPC de la llamada.

        Returns:
            DevolucionResponse con resultado de la devolución.
        """
        isbn = request.isbn.strip()
        if not isbn:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("El ISBN no puede estar vacío.")
            return pb2.DevolucionResponse(ok=False, mensaje="El ISBN no puede estar vacío.", disponibles=0)

        with self.repo.with_lock():
            try:
                libros = self.repo.cargar()
                libro = self.repo.buscar_por_isbn(libros, isbn)
                if not libro:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(f"No existe un libro con ISBN: {isbn}")
                    return pb2.DevolucionResponse(ok=False, mensaje="No existe un libro con ese ISBN.", disponibles=0)

                if libro.prestados <= 0:
                    context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                    context.set_details("No hay préstamos registrados para devolver.")
                    return pb2.DevolucionResponse(
                        ok=False,
                        mensaje="No hay préstamos registrados para devolver.",
                        disponibles=libro.disponibles,
                    )

                libro.prestados -= 1
                self.repo.guardar(libros)

                logger.info(
                    "Devolución registrada — ISBN: %s, Título: %s, Disponibles: %d",
                    libro.isbn, libro.titulo, libro.disponibles,
                )
                return pb2.DevolucionResponse(
                    ok=True,
                    mensaje="Devolución registrada.",
                    disponibles=libro.disponibles,
                )
            except Exception as error:
                logger.exception("Error al devolver ISBN %s", isbn)
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(str(error))
                return pb2.DevolucionResponse(ok=False, mensaje=f"Error devolviendo: {error}", disponibles=0)


def serve() -> None:
    """Inicia el servidor gRPC en el puerto 50051.

    Crea el repositorio de datos, registra el servicio y espera
    conexiones de clientes. Soporta hasta 10 clientes concurrentes.
    """
    repo = RepositorioTxtBiblioteca("biblioteca.txt")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_BibliotecaServiceServicer_to_server(BibliotecaService(repo), server)

    server.add_insecure_port("[::]:50051")
    server.start()
    logger.info("Servidor gRPC activo en puerto 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
