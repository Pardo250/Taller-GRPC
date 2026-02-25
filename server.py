from concurrent import futures
import grpc
from datetime import date, timedelta

import biblioteca_pb2 as pb2
import biblioteca_pb2_grpc as pb2_grpc

from repo_txt import RepositorioTxtBiblioteca


class BibliotecaService(pb2_grpc.BibliotecaServiceServicer):
    def __init__(self, repo: RepositorioTxtBiblioteca):
        self.repo = repo

    def ConsultarPorIsbn(self, request: pb2.ConsultaRequest, context):
        try:
            libros = self.repo.cargar()
            l = self.repo.buscar_por_isbn(libros, request.isbn)
            if not l:
                return pb2.ConsultaResponse(existe=False, mensaje="No existe un libro con ese ISBN.")
            return pb2.ConsultaResponse(
                existe=True,
                mensaje="Libro encontrado.",
                isbn=l.isbn,
                titulo=l.titulo,
                autor=l.autor,
                total=l.total,
                prestados=l.prestados,
                disponibles=l.disponibles,
            )
        except Exception as e:
            return pb2.ConsultaResponse(existe=False, mensaje=f"Error consultando: {e}")

    def PrestarPorIsbn(self, request: pb2.PrestamoIsbnRequest, context):
        with self.repo.with_lock():
            try:
                libros = self.repo.cargar()
                l = self.repo.buscar_por_isbn(libros, request.isbn)
                if not l:
                    return pb2.PrestamoResponse(ok=False, mensaje="No existe un libro con ese ISBN.")

                if l.disponibles <= 0:
                    return pb2.PrestamoResponse(ok=False, mensaje="No hay ejemplares disponibles.")

                l.prestados += 1
                self.repo.guardar(libros)

                fecha_dev = (date.today() + timedelta(days=7)).isoformat()
                return pb2.PrestamoResponse(
                    ok=True,
                    mensaje="Préstamo realizado.",
                    fecha_devolucion=fecha_dev,
                    disponibles_restantes=l.disponibles,
                )
            except Exception as e:
                return pb2.PrestamoResponse(ok=False, mensaje=f"Error prestando: {e}")

    def PrestarPorTitulo(self, request: pb2.PrestamoTituloRequest, context):
        with self.repo.with_lock():
            try:
                libros = self.repo.cargar()
                l = self.repo.buscar_por_titulo(libros, request.titulo)
                if not l:
                    return pb2.PrestamoResponse(ok=False, mensaje="No existe un libro con ese título.")

                if l.disponibles <= 0:
                    return pb2.PrestamoResponse(ok=False, mensaje="No hay ejemplares disponibles.")

                l.prestados += 1
                self.repo.guardar(libros)

                fecha_dev = (date.today() + timedelta(days=7)).isoformat()
                return pb2.PrestamoResponse(
                    ok=True,
                    mensaje="Préstamo realizado.",
                    fecha_devolucion=fecha_dev,
                    disponibles_restantes=l.disponibles,
                )
            except Exception as e:
                return pb2.PrestamoResponse(ok=False, mensaje=f"Error prestando: {e}")

    def DevolverPorIsbn(self, request: pb2.DevolucionRequest, context):
        with self.repo.with_lock():
            try:
                libros = self.repo.cargar()
                l = self.repo.buscar_por_isbn(libros, request.isbn)
                if not l:
                    return pb2.DevolucionResponse(ok=False, mensaje="No existe un libro con ese ISBN.", disponibles=0)

                if l.prestados <= 0:
                    return pb2.DevolucionResponse(ok=False, mensaje="No hay préstamos registrados para devolver.", disponibles=l.disponibles)

                l.prestados -= 1
                self.repo.guardar(libros)

                return pb2.DevolucionResponse(ok=True, mensaje="Devolución registrada.", disponibles=l.disponibles)
            except Exception as e:
                return pb2.DevolucionResponse(ok=False, mensaje=f"Error devolviendo: {e}", disponibles=0)


def serve():
    repo = RepositorioTxtBiblioteca("biblioteca.txt")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_BibliotecaServiceServicer_to_server(BibliotecaService(repo), server)

    server.add_insecure_port("[::]:50051")
    server.start()
    print("✅ Servidor gRPC activo en puerto 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
