"""
test_server.py — Tests de integración para el servidor gRPC de la biblioteca.

Inicia un servidor gRPC en un hilo separado con un repositorio temporal
y verifica las respuestas de cada endpoint del servicio.

Ejecutar con:
    python -m pytest test_server.py -v
"""

import os
import tempfile
import threading
import time
from concurrent import futures
from pathlib import Path

import grpc
import pytest

import biblioteca_pb2 as pb2
import biblioteca_pb2_grpc as pb2_grpc
from repo_txt import RepositorioTxtBiblioteca
from server import BibliotecaService


# Puerto aleatorio para evitar conflictos durante los tests
TEST_PORT = "50055"
TEST_ADDRESS = f"localhost:{TEST_PORT}"


@pytest.fixture(scope="module")
def grpc_server():
    """Configura e inicia el servidor gRPC para los tests."""
    # 1. Crear archivo temporal con datos iniciales
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("9780134685991|Effective Java|Joshua Bloch|5|2\n")
        f.write("9781492078005|Designing Data|Martin Kleppmann|3|3\n") # Agotado
        ruta_txt = f.name

    repo = RepositorioTxtBiblioteca(ruta_txt)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    pb2_grpc.add_BibliotecaServiceServicer_to_server(BibliotecaService(repo), server)
    server.add_insecure_port(f"[::]:{TEST_PORT}")
    server.start()

    # Dar un pequeño margen para que el servidor inicie
    time.sleep(0.5)

    yield TEST_ADDRESS

    server.stop(0)
    if os.path.exists(ruta_txt):
        os.unlink(ruta_txt)


@pytest.fixture(scope="module")
def stub(grpc_server):
    """Crea el stub de comunicación con el servidor gRPC."""
    channel = grpc.insecure_channel(grpc_server)
    return pb2_grpc.BibliotecaServiceStub(channel)


# ── Tests de Consulta ───────────────────────────────────────────


def test_consultar_isbn_exitoso(stub):
    response = stub.ConsultarPorIsbn(pb2.ConsultaRequest(isbn="9780134685991"))
    assert response.existe is True
    assert "Java" in response.titulo
    assert response.disponibles == 3


def test_consultar_isbn_inexistente(stub):
    with pytest.raises(grpc.RpcError) as e:
        stub.ConsultarPorIsbn(pb2.ConsultaRequest(isbn="0000000000000"))
    assert e.value.code() == grpc.StatusCode.NOT_FOUND


def test_consultar_isbn_vacio(stub):
    with pytest.raises(grpc.RpcError) as e:
        stub.ConsultarPorIsbn(pb2.ConsultaRequest(isbn=" "))
    assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT


# ── Tests de Préstamo ───────────────────────────────────────────


def test_prestar_por_isbn_exitoso(stub):
    response = stub.PrestarPorIsbn(pb2.PrestamoIsbnRequest(isbn="9780134685991"))
    assert response.ok is True
    assert response.disponibles_restantes == 2
    assert response.fecha_devolucion != ""


def test_prestar_por_isbn_sin_disponibilidad(stub):
    # El libro 9781492078005 inicia con 3/3 prestados (0 disponibles)
    with pytest.raises(grpc.RpcError) as e:
        stub.PrestarPorIsbn(pb2.PrestamoIsbnRequest(isbn="9781492078005"))
    assert e.value.code() == grpc.StatusCode.FAILED_PRECONDITION


def test_prestar_por_titulo_exitoso(stub):
    # Nota: Usamos "Effective Java" que ahora tiene 2 disponibles tras el test anterior
    response = stub.PrestarPorTitulo(pb2.PrestamoTituloRequest(titulo="Effective Java"))
    assert response.ok is True
    assert response.disponibles_restantes == 1


# ── Tests de Devolución ─────────────────────────────────────────


def test_devolver_por_isbn_exitoso(stub):
    # El libro 9780134685991 tiene 4 prestados ahora (2 iniciales + 2 de los tests de arriba)
    response = stub.DevolverPorIsbn(pb2.DevolucionRequest(isbn="9780134685991"))
    assert response.ok is True
    assert response.disponibles == 2 # 5 total - 3 prestados


def test_devolver_sin_prestamos_previos(stub):
    # El libro 9781492078005 está 3/3 (prestados/total)
    # Devolverlo debería funcionar y dejarlo en 2 prestados (1 disponible)
    response = stub.DevolverPorIsbn(pb2.DevolucionRequest(isbn="9781492078005"))
    assert response.ok is True
    assert response.disponibles == 1
