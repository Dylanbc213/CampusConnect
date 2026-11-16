# CampusConnect

CampusConnect es una red social estudiantil desarrollada en Python con interfaz gráfica Tkinter. La aplicación permite gestionar usuarios, amistades, publicaciones, fotos, videos y temas visuales, todo con persistencia local en archivos JSON.

## Características principales

- Registro e inicio de sesión de usuarios
- Perfil de estudiante con información y avatar
- Seguimiento de amistades entre usuarios
- Feed de publicaciones con texto, imágenes y videos
- Interfaz con modo claro y oscuro
- Persistencia local de datos en archivos JSON
- Reproductor de video integrado para publicaciones multimedia
- Gestión de publicaciones con validación de contenido, imagen y caracteres

## Stack tecnológico

- Python 3
- Tkinter
- Pillow
- python-vlc
- JSON para persistencia de datos

## Requisitos previos

- Python 3.10 o superior
- VLC de 64 bits instalado en el sistema
- La librería `python-vlc` disponible en el entorno del proyecto

Instala VLC desde:
https://www.videolan.org/vlc/

## Instalación

1. Clona el repositorio:

```bash
git clone https://github.com/Dylanbc213/CampusConnect.git
cd CampusConnect
```

2. Crea un entorno virtual (opcional pero recomendado):

```bash
python -m venv .venv
```

3. Activa el entorno virtual:

- Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

- Windows (cmd):

```cmd
.venv\Scripts\activate.bat
```

- Linux/macOS:

```bash
source .venv/bin/activate
```

4. Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Ejecución

Inicia la aplicación con:

```bash
python main.py
```

## Estructura del proyecto

```text
CampusConnect/
├── datos/                     # Archivos de persistencia local
├── gestores/                  # Lógica de usuarios, publicaciones, amistades, configuración
├── gui/                       # Vistas y estilos de la interfaz
├── modelos/                   # Modelos de dominio
├── persistencia/              # Módulos de auditoría y almacenamiento
├── main.py                    # Punto de entrada de la aplicación
├── requirements.txt           # Dependencias del proyecto
├── pruebas_*.py               # Pruebas unitarias del sistema
├── README.md                  # Documentación del proyecto
└── .gitignore                 # Ignorar archivos temporales y locales
```

## Consideraciones sobre video

La aplicación incluye un reproductor de video integrado para publicaciones. Para que funcione correctamente:

- Debe tener instalado VLC de 64 bits
- El reproductor se encarga de reproducir, pausar, detener y controlar el volumen dentro de la interfaz
- Al salir de la vista, el video se detiene automáticamente
- No se abre un reproductor externo independiente

## Ejecutar pruebas

El proyecto incluye varias pruebas unitarias. Puedes ejecutarlas con:

```bash
python -m unittest
```

O ejecutar pruebas específicas:

```bash
python -m unittest pruebas_tema.py
python -m unittest pruebas_publicaciones.py
```

## Estado del proyecto

CampusConnect es una aplicación de tipo red social académica orientada a un entorno local y de práctica, con una interfaz gráfica más enfocada en funcionalidad que en un despliegue web.

## Autor

Proyecto desarrollado en el contexto de estructuras de datos y programación orientada a objetos.
