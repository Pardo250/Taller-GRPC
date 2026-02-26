# 📚 Sistema de Biblioteca — gRPC

Sistema de gestión de biblioteca remoto implementado con **Python 3** y **gRPC** para el taller de Introducción a Sistemas Distribuidos (Febrero 2026).

---

## Descripción

Servicio remoto que permite realizar operaciones de **préstamo**, **devolución** y **consulta** de libros sobre una base de datos de archivo plano (`biblioteca.txt`). La comunicación cliente-servidor se realiza mediante Protocol Buffers y gRPC con operaciones síncronas.

### Operaciones Disponibles

| Operación | Descripción |
|---|---|
| **Consultar por ISBN** | Verifica si un libro existe y muestra ejemplares disponibles |
| **Préstamo por ISBN** | Registra un préstamo dado el ISBN; retorna fecha de devolución (7 días) |
| **Préstamo por Título** | Registra un préstamo dado el título exacto; retorna fecha de devolución |
| **Devolución por ISBN** | Registra la devolución de un libro previamente prestado |

---

## Requisitos Previos

- **Python 3.8+** instalado
- **pip** (gestor de paquetes de Python)
- Conexión de red entre máquinas (si se ejecuta en computadoras diferentes)

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Pardo250/Taller-GRPC.git
cd Taller-GRPC
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install grpcio grpcio-tools
```

### 4. Compilar el archivo `.proto`

Este paso genera los archivos `biblioteca_pb2.py` y `biblioteca_pb2_grpc.py` necesarios para la comunicación gRPC:

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. biblioteca.proto
```

> **Nota:** Los archivos generados (`*_pb2.py`, `*_pb2_grpc.py`) están en `.gitignore`, por lo que **este paso es obligatorio** tras clonar el repositorio.

---

## Ejecución

### En una sola máquina (pruebas locales)

**Terminal 1 — Servidor:**
```bash
python server.py
```
Salida esperada:
```
✅ Servidor gRPC activo en puerto 50051
```

**Terminal 2 — Cliente:**
```bash
python client.py
```
Se mostrará un menú interactivo:
```
--- MENÚ ---
1) Consultar por ISBN
2) Prestar por ISBN
3) Prestar por Título
4) Devolver por ISBN
0) Salir
Opción:
```

### Tests

```bash
# Tests unitarios del repositorio y modelos
python -m pytest test_repo.py -v

# Tests de integración del servidor gRPC
python -m pytest test_server.py -v
```

### En dos computadoras diferentes

1. **En la máquina servidor** (donde está la BD):
   ```bash
   python server.py
   ```

2. **En la máquina cliente**, modificar la línea 7 de `client.py`:
   ```python
   # Cambiar "localhost" por la IP del servidor
   channel = grpc.insecure_channel("192.168.x.x:50051")
   ```
   Luego ejecutar:
   ```bash
   python client.py
   ```

> **Importante:** Asegúrese de que el puerto `50051` esté abierto en el firewall de la máquina servidor.

---

## Estructura del Proyecto

```
Taller-GRPC/
├── biblioteca.proto          # Definición del servicio gRPC (contrato)
├── server.py                 # Servidor gRPC con la lógica de negocio
├── client.py                 # Cliente CLI interactivo
├── repo_txt.py               # Capa de persistencia (repositorio TXT)
├── models.py                 # Definición de la entidad Libro y validaciones
├── test_repo.py              # Tests unitarios de repositorio y modelos
├── test_server.py            # Tests de integración del servidor gRPC
├── reporte_entrega_taller_grpc.md # Reporte formal de entrega
├── biblioteca.txt            # Base de datos de libros (10 registros)
├── .gitignore                # Ignora archivos generados y caché
├── Taller_MRI_2026.pdf       # Instrucciones del taller
└── README.md                 # Este archivo
```

## Modelo de Datos

Cada libro en `biblioteca.txt` sigue el formato:

```
ISBN|TITULO|AUTOR|TOTAL_EJEMPLARES|PRESTADOS
```

**Ejemplo:**
```
9780134685991|Effective Java|Joshua Bloch|5|2
```

Los **disponibles** se calculan como `TOTAL - PRESTADOS`.

---

## Arquitectura

```
┌──────────────┐        gRPC / Protobuf        ┌──────────────────┐
│   client.py  │ ────────────────────────────►  │    server.py     │
│  (CLI Menú)  │ ◄────────────────────────────  │  (BibliotecaServ)│
└──────────────┘       Puerto 50051             └────────┬─────────┘
                                                         │
                                                         ▼
                                                ┌──────────────────┐
                                                │   repo_txt.py    │
                                                │  (Repositorio)   │
                                                └────────┬─────────┘
                                                         │
                                                         ▼
                                                ┌──────────────────┐
                                                │ biblioteca.txt   │
                                                │   (BD plana)     │
                                                └──────────────────┘
```

---

## Ejemplo de Uso

### Consultar un libro
```
Opción: 1
ISBN: 9780134685991
Libro encontrado.
Título: Effective Java
Autor: Joshua Bloch
Total: 5 | Prestados: 2 | Disponibles: 3
```

### Prestar un libro
```
Opción: 2
ISBN: 9780134685991
Préstamo realizado.
Fecha devolución: 2026-03-05
Disponibles restantes: 2
```

### Devolver un libro
```
Opción: 4
ISBN: 9780134685991
Devolución registrada.
Disponibles ahora: 3
```

---

## Concurrencia

El servidor soporta **hasta 10 clientes simultáneos** mediante `ThreadPoolExecutor(max_workers=10)`. Las operaciones de escritura (préstamo y devolución) están protegidas con `threading.Lock` para garantizar integridad de datos.

---

## Tecnologías

- **Python 3** — Lenguaje de programación
- **gRPC** — Framework de comunicación remota (RPC)
- **Protocol Buffers** — Serialización de mensajes
- **Threading** — Concurrencia en el servidor

---

## Autores

Taller de Introducción a Sistemas Distribuidos — Facultad de Ingeniería, Departamento de Ingeniería de Sistemas.
