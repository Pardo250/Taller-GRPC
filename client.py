"""
client.py — Cliente CLI interactivo para el sistema de biblioteca gRPC.

Conecta al servidor gRPC y presenta un menú de opciones para
consultar, prestar y devolver libros.
"""

import sys

import grpc

import biblioteca_pb2 as pb2
import biblioteca_pb2_grpc as pb2_grpc


def mostrar_menu() -> None:
    """Imprime el menú de opciones disponibles."""
    print("\n--- MENÚ BIBLIOTECA ---")
    print("1) Consultar por ISBN")
    print("2) Prestar por ISBN")
    print("3) Prestar por Título")
    print("4) Devolver por ISBN")
    print("0) Salir")


def consultar_por_isbn(stub: pb2_grpc.BibliotecaServiceStub) -> None:
    """Solicita un ISBN y muestra la información del libro.

    Args:
        stub: Stub del servicio gRPC.
    """
    isbn = input("ISBN: ").strip()
    if not isbn:
        print("⚠️  El ISBN no puede estar vacío.")
        return
    respuesta = stub.ConsultarPorIsbn(pb2.ConsultaRequest(isbn=isbn))
    print(respuesta.mensaje)
    if respuesta.existe:
        print(f"  Título:      {respuesta.titulo}")
        print(f"  Autor:       {respuesta.autor}")
        print(f"  Total:       {respuesta.total}")
        print(f"  Prestados:   {respuesta.prestados}")
        print(f"  Disponibles: {respuesta.disponibles}")


def prestar_por_isbn(stub: pb2_grpc.BibliotecaServiceStub) -> None:
    """Solicita un ISBN y registra un préstamo.

    Args:
        stub: Stub del servicio gRPC.
    """
    isbn = input("ISBN: ").strip()
    if not isbn:
        print("⚠️  El ISBN no puede estar vacío.")
        return
    respuesta = stub.PrestarPorIsbn(pb2.PrestamoIsbnRequest(isbn=isbn))
    print(respuesta.mensaje)
    if respuesta.ok:
        print(f"  Fecha devolución:     {respuesta.fecha_devolucion}")
        print(f"  Disponibles restantes: {respuesta.disponibles_restantes}")


def prestar_por_titulo(stub: pb2_grpc.BibliotecaServiceStub) -> None:
    """Solicita un título y registra un préstamo.

    Args:
        stub: Stub del servicio gRPC.
    """
    titulo = input("Título exacto: ").strip()
    if not titulo:
        print("⚠️  El título no puede estar vacío.")
        return
    respuesta = stub.PrestarPorTitulo(pb2.PrestamoTituloRequest(titulo=titulo))
    print(respuesta.mensaje)
    if respuesta.ok:
        print(f"  Fecha devolución:     {respuesta.fecha_devolucion}")
        print(f"  Disponibles restantes: {respuesta.disponibles_restantes}")


def devolver_por_isbn(stub: pb2_grpc.BibliotecaServiceStub) -> None:
    """Solicita un ISBN y registra la devolución del libro.

    Args:
        stub: Stub del servicio gRPC.
    """
    isbn = input("ISBN: ").strip()
    if not isbn:
        print("⚠️  El ISBN no puede estar vacío.")
        return
    respuesta = stub.DevolverPorIsbn(pb2.DevolucionRequest(isbn=isbn))
    print(respuesta.mensaje)
    if respuesta.ok:
        print(f"  Disponibles ahora: {respuesta.disponibles}")


def main() -> None:
    """Punto de entrada del cliente.

    Establece la conexión gRPC y ejecuta el bucle del menú interactivo.
    Maneja errores de conexión y desconexiones del servidor.
    """
    direccion = "localhost:50051"
    print(f"Conectando al servidor gRPC en {direccion}...")

    try:
        channel = grpc.insecure_channel(direccion)
        stub = pb2_grpc.BibliotecaServiceStub(channel)
    except Exception as error:
        print(f"❌ Error al conectar con el servidor: {error}")
        sys.exit(1)

    opciones = {
        "1": consultar_por_isbn,
        "2": prestar_por_isbn,
        "3": prestar_por_titulo,
        "4": devolver_por_isbn,
    }

    while True:
        mostrar_menu()
        opcion = input("Opción: ").strip()

        if opcion == "0":
            print("👋 ¡Hasta luego!")
            break

        accion = opciones.get(opcion)
        if accion:
            try:
                accion(stub)
            except grpc.RpcError as error:
                print(f"❌ Error de comunicación con el servidor: {error.details()}")
                print(f"   Código: {error.code().name}")
        else:
            print("⚠️  Opción inválida. Intente de nuevo.")


if __name__ == "__main__":
    main()
