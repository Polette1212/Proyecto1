# GameVault

Sistema web de gestión y catálogo de videojuegos desarrollado con Django.

## Descripción

GameVault es una aplicación web orientada a la gestión de videojuegos, usuarios y operaciones de compra.

El sistema incorpora autenticación, autorización por roles, catálogo de videojuegos, carrito de compras, pedidos, control de acceso y administración mediante Django.

## Tecnologías

- Python 3.13
- Django 6.1
- SQLite para desarrollo
- MySQL para producción
- Bootstrap
- HTML5
- CSS3
- JavaScript
- Git
- GitHub

## Funcionalidades

- Registro e inicio de sesión.
- Catálogo y búsqueda de videojuegos.
- Gestión de videojuegos.
- Gestión de perfiles gamer.
- Carrito de compras.
- Proceso de compra.
- Gestión de pedidos.
- Historial de pedidos.
- Comprobante de compra.
- Control de stock.
- Control de acceso.
- Restricción horaria.
- Roles Administrador, Operador y Consulta.
- Panel administrativo.
- Gestión de usuarios.
- Carga de imágenes.
- Carga de archivos técnicos.

## Roles

### Administrador

Puede crear, consultar, modificar y eliminar información según las funciones administrativas del sistema.

### Operador

Puede consultar, crear y modificar información operativa, pero no puede administrar usuarios ni eliminar información crítica.

### Consulta

Puede visualizar y buscar información, sin permisos para crear, modificar o eliminar registros.

## Base de datos

El proyecto utiliza Django ORM y migraciones.

Durante el desarrollo se utiliza SQLite. La configuración también contempla MySQL mediante variables de entorno para producción.

## Variables de entorno

`	ext
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
DJANGO_ALLOWED_HOSTS=
DB_ENGINE=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
