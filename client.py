import grpc
import biblioteca_pb2 as pb2
import biblioteca_pb2_grpc as pb2_grpc


def main():
    channel = grpc.insecure_channel("localhost:50051")
    stub = pb2_grpc.BibliotecaServiceStub(channel)

    while True:
        print("\n--- MENÚ ---")
        print("1) Consultar por ISBN")
        print("2) Prestar por ISBN")
        print("3) Prestar por Título")
        print("4) Devolver por ISBN")
        print("0) Salir")
        op = input("Opción: ").strip()

        if op == "0":
            break

        if op == "1":
            isbn = input("ISBN: ").strip()
            r = stub.ConsultarPorIsbn(pb2.ConsultaRequest(isbn=isbn))
            print(r.mensaje)
            if r.existe:
                print(f"Título: {r.titulo}")
                print(f"Autor: {r.autor}")
                print(f"Total: {r.total} | Prestados: {r.prestados} | Disponibles: {r.disponibles}")

        elif op == "2":
            isbn = input("ISBN: ").strip()
            r = stub.PrestarPorIsbn(pb2.PrestamoIsbnRequest(isbn=isbn))
            print(r.mensaje)
            if r.ok:
                print(f"Fecha devolución: {r.fecha_devolucion}")
                print(f"Disponibles restantes: {r.disponibles_restantes}")

        elif op == "3":
            titulo = input("Título exacto: ").strip()
            r = stub.PrestarPorTitulo(pb2.PrestamoTituloRequest(titulo=titulo))
            print(r.mensaje)
            if r.ok:
                print(f"Fecha devolución: {r.fecha_devolucion}")
                print(f"Disponibles restantes: {r.disponibles_restantes}")

        elif op == "4":
            isbn = input("ISBN: ").strip()
            r = stub.DevolverPorIsbn(pb2.DevolucionRequest(isbn=isbn))
            print(r.mensaje)
            if r.ok:
                print(f"Disponibles ahora: {r.disponibles}")
        else:
            print("Opción inválida.")


if __name__ == "__main__":
    main()
