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


## 1. Perfiles personalizables y perfiles de otros usuarios
**Esfuerzo: Medium**

```text
Agrega perfiles personalizables a CampusConnect, inspirados en Instagram y con la estética de la UNA.

1. Crea "Mi perfil" dentro de la ventana principal, sin abrir ventanas adicionales.
2. Permite editar nombre visible, biografía de máximo 150 caracteres y foto de perfil opcional.
3. Conserva el @usuario como identificador único.
4. Muestra avatar, nombre, usuario, biografía, contador de amigos y publicaciones propias.
5. Permite visitar perfiles desde el buscador, la lista de amigos y el autor de publicaciones.
6. En perfiles ajenos muestra datos públicos, publicaciones y estado de amistad.
7. Permite agregar amigos desde otros perfiles reutilizando GestorAmistades.
8. Solo el propietario puede editar su perfil.
9. Guarda los cambios en JSON, manteniendo compatibilidad con usuarios existentes.
10. Para las fotos, usa archivos locales y rutas relativas; valida formato y tamaño. Si requieren dependencias nuevas, usa avatares con iniciales.
11. Mantén una sola ventana con navegación por frames.
12. Conserva la estética UNA: rojo #E4002B, blanco, gris claro y tarjetas modernas.
13. Prueba edición, persistencia y permisos.

RESTRICCIONES:
- Reutiliza clases y gestores existentes.
- Mantén Python, Tkinter y JSON.
- No agregues dependencias externas.
- No desarrolles likes, comentarios, mensajería, notificaciones ni ordenamiento del feed en esta tarea.
- No borres datos ni afectes otras funcionalidades.

AHORRO DE TOKENS:
Inspecciona solo archivos necesarios. Haz cambios mínimos y evita refactorizaciones.
Ejecuta pruebas relevantes. Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 2. Botón Editar perfil
**Esfuerzo: Medium**

```text
Agrega y haz funcional el botón "Editar perfil" en la sección "Mi perfil" de CampusConnect.

1. Muestra "Editar perfil" junto al nombre o avatar del usuario autenticado, con estilo moderno UNA.
2. Al presionarlo, abre un formulario dentro de la misma ventana, sin crear ventanas adicionales.
3. Permite editar nombre visible, biografía de máximo 150 caracteres y foto si ya se admiten imágenes; de lo contrario, conserva el avatar con iniciales.
4. Agrega botones "Guardar cambios" y "Cancelar".
5. Carga los datos actuales y valida campos.
6. Guarda los cambios en JSON sin alterar usuario, contraseña, identificadores ni amistades.
7. Actualiza inmediatamente el nombre y avatar en perfil, buscador, amigos y publicaciones.
8. Solo el propietario puede editar su perfil.
9. Muestra mensajes de éxito y error sin perder datos anteriores si falla el guardado.
10. Mantén el diseño moderno tipo Instagram con rojo UNA #E4002B, blanco y gris claro.

RESTRICCIONES:
- Reutiliza clases y componentes existentes.
- Mantén Python, Tkinter, ttk y JSON sin dependencias externas.
- No desarrolles funcionalidades de otras fases.
- Conserva la navegación en una sola ventana.

AHORRO DE TOKENS:
Revisa solo archivos necesarios y haz cambios mínimos.
Prueba edición, guardado, cancelación y persistencia.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 3. Inicio, publicaciones y comentarios
**Esfuerzo: Medium**

```text
Mejora el inicio y las publicaciones de CampusConnect.

1. En Inicio, muestra mis publicaciones y las de mis amigos, sin duplicarlas.
2. Al publicar, actualiza automáticamente las vistas correspondientes sin reiniciar.
3. Agrega un botón "Actualizar" para recargar manualmente desde JSON.
4. Permite responder a publicaciones con comentarios que muestren autor, fecha y contenido.
5. Permite expandir y contraer comentarios.
6. Guarda comentarios en JSON, manteniendo compatibilidad con publicaciones existentes.
7. Valida comentarios vacíos y utiliza el usuario autenticado como autor.
8. Muestra comentarios nuevos inmediatamente.
9. Reutiliza un mismo componente visual de publicaciones para Inicio, Mi muro y perfiles.
10. Mantén tarjetas modernas, avatares y estética UNA.

RESTRICCIONES:
- Mantén Python, Tkinter, ttk y JSON, sin dependencias externas.
- Conserva una sola ventana con navegación interna.
- No implementes notificaciones, mensajería ni ordenamiento avanzado del feed en esta tarea.
- No elimines datos; mantén compatibilidad con JSON antiguos.

AHORRO DE TOKENS:
Revisa solo archivos necesarios; reutiliza componentes y evita refactorizaciones.
Prueba publicación, actualización, comentarios y persistencia.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 4. Perfiles ajenos y publicaciones unificadas
**Esfuerzo: Medium**

```text
Mejora los perfiles y las publicaciones de CampusConnect.

1. Permite abrir perfiles desde el buscador, amigos y autores de publicaciones o comentarios.
2. Muestra nombre, @usuario, avatar, biografía, cantidad de amigos y publicaciones.
3. Muestra las publicaciones del perfil exactamente igual que en Inicio, incluyendo comentarios.
4. Reutiliza un único componente visual de publicaciones para todas las secciones.
5. Permite responder desde cualquier vista.
6. Actualiza automáticamente publicaciones y comentarios; conserva recarga manual.
7. Permite agregar amigos desde perfiles ajenos y muestra "Amigos" cuando corresponda.
8. Solo el propietario puede editar su perfil.
9. Agrega navegación "Volver" sin ventanas nuevas.
10. Mantén estética UNA y estilo tipo Instagram.

RESTRICCIONES:
- Reutiliza clases, gestores y componentes existentes.
- No dupliques sistemas de perfiles o publicaciones.
- Mantén Python, Tkinter, ttk y JSON sin dependencias externas.
- Conserva todos los datos existentes.

AHORRO DE TOKENS:
Revisa solo archivos necesarios y haz cambios mínimos.
Prueba navegación, permisos, publicaciones y comentarios.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 5. Orden cronológico: más recientes primero
**Esfuerzo: Low**

```text
Ordena todas las publicaciones de CampusConnect de la más reciente a la más antigua.

1. Muestra primero las publicaciones nuevas.
2. Aplica el orden en Inicio, Mi muro y perfiles.
3. Ordena usando fecha y hora real de creación, no la posición dentro del JSON.
4. Al publicar, muestra la nueva publicación automáticamente en la primera posición.
5. Mantén el orden al presionar "Actualizar".
6. Si coinciden las fechas, usa un criterio estable.
7. Conserva los comentarios de cada publicación.
8. Maneja fechas inválidas sin provocar errores.

RESTRICCIONES:
- Reutiliza GestorPublicaciones y la GUI existente.
- Mantén Python, Tkinter y JSON.
- No alteres datos ni estructura JSON, diseño ni otras funcionalidades.
- No agregues dependencias.

AHORRO DE TOKENS:
Revisa solo archivos necesarios y haz cambios mínimos.
Prueba el orden, publicación nueva y recarga manual.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 6. Rueda del mouse y Enter para publicar
**Esfuerzo: Low**

```text
Mejora la navegación y publicación en CampusConnect.

1. Permite usar la rueda del mouse para desplazarse en Inicio, Mi muro, perfiles, amigos y buscador.
2. El scroll debe funcionar incluso con el cursor sobre tarjetas, textos o publicaciones.
3. Evita desplazamientos duplicados o que afecten otras secciones.
4. Permite publicar con Enter cuando el campo de nueva publicación tenga el foco.
5. Usa Shift+Enter para insertar saltos de línea.
6. Evita publicaciones vacías o duplicadas.
7. No interfieras con comentarios, búsquedas ni otros campos.
8. Conserva el botón Publicar y la actualización automática del muro.

RESTRICCIONES:
- Mantén Python, Tkinter y ttk.
- Reutiliza componentes, una sola ventana y los JSON existentes.
- No modifiques otras funciones.

AHORRO DE TOKENS:
Revisa solo archivos GUI necesarios; haz cambios mínimos.
Prueba scroll, Enter y Shift+Enter.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 7. Publicaciones con foto e imagen más comentario
**Esfuerzo: Medium**

```text
Mejora el sistema de publicaciones de CampusConnect para permitir publicaciones con texto e imagen.

1. Permite publicar solo texto, solo imagen o ambos.
2. Agrega botón para seleccionar imagen local.
3. Valida formatos compatibles con Tkinter/Pillow.
4. Guarda autor, fecha, texto y referencia de imagen.
5. Mantén compatibilidad con publicaciones antiguas.
6. Muestra imágenes en tarjetas con buen tamaño y proporción.
7. Conserva orden de más reciente a más antigua.
8. Actualiza Inicio, Mi muro y perfiles al publicar.
9. Conserva recarga manual.
10. Maneja imágenes faltantes o dañadas sin cerrar la aplicación.

RESTRICCIONES:
- Python, Tkinter, ttk y JSON; dependencias nuevas solo si son necesarias.
- Reutiliza GestorPublicaciones, el modelo y componentes actuales.
- No rompas datos anteriores ni abras ventanas adicionales.

AHORRO DE TOKENS:
Revisa solo archivos relacionados, haz cambios mínimos y prueba creación, visualización y persistencia.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 8. Reacciones: Me gusta, Me divierte, No me gusta; respuestas con imágenes
**Esfuerzo: Medium**

```text
Agrega reacciones y respuestas a las publicaciones de CampusConnect.

1. Implementa únicamente tres reacciones: Me gusta, Me divierte y No me gusta.
2. Cada usuario puede tener una sola reacción activa por publicación.
3. Permite cambiar o quitar la reacción seleccionada.
4. Muestra contadores individuales y destaca la reacción seleccionada.
5. Permite responder con texto, imagen o ambos.
6. Guarda autor, fecha, texto e imagen de cada respuesta.
7. Permite expandir o contraer las respuestas.
8. Actualiza las interacciones automáticamente.
9. Muestra las mismas tarjetas en Inicio, Mi muro y perfiles.
10. Guarda todo en JSON sin romper datos anteriores.
11. Reutiliza el soporte de imágenes existente con rutas relativas.
12. Prueba contadores, cambios de reacción, eliminación de reacción y persistencia.

RESTRICCIONES:
- Mantén Python, Tkinter, ttk y JSON.
- Reutiliza clases y componentes existentes.
- Conserva estética UNA y una sola ventana.
- No agregues otras reacciones, mensajería ni dependencias innecesarias en esta tarea.

AHORRO DE TOKENS:
Revisa solo archivos relacionados y haz cambios mínimos.
Ejecuta pruebas relevantes. Resume resultados en máximo 5 líneas.
No hagas commits ni push.
```

## 9. Foto de perfil y vista previa antes de publicar
**Esfuerzo: Medium**

```text
Mejora las imágenes de CampusConnect.

FOTO DE PERFIL:
1. Permite subir y cambiar fotos desde "Editar perfil".
2. Acepta JPG, JPEG, PNG, WEBP y GIF.
3. Muestra una vista previa antes de guardar.
4. Usa avatares circulares sin deformar imágenes.
5. Muestra la foto en perfiles, buscador, amigos, publicaciones y comentarios.
6. Si no hay foto, utiliza iniciales.
7. Actualiza los avatares después de guardar.

PUBLICACIONES:
8. Muestra una vista previa antes de publicar.
9. Permite quitar o cambiar la imagen seleccionada.
10. Ajusta la imagen al espacio sin deformarla.
11. Admite texto, imagen o ambos.
12. Conserva Enter para publicar y Shift+Enter para saltos de línea.
13. Limpia el formulario y actualiza el muro después de publicar.

RESPUESTAS:
14. Agrega vista previa a imágenes de comentarios si ya existe esa funcionalidad.

FORMATOS Y DATOS:
15. Usa Pillow si existe o es necesario para soportar todos los formatos.
16. Para GIF muestra el primer fotograma.
17. Valida contenido real y tamaño máximo de 10 MB.
18. Guarda imágenes en carpetas locales con nombres únicos y referencias relativas en JSON.
19. Conserva compatibilidad con datos anteriores.
20. Maneja imágenes faltantes o dañadas sin errores.

RESTRICCIONES:
- Mantén Python, Tkinter, ttk y JSON, usando Pillow si hace falta.
- Reutiliza gestores y componentes; estética UNA y navegación integrada.
- No modifiques otras funcionalidades ni borres datos.

AHORRO DE TOKENS:
Revisa solo archivos necesarios y haz cambios mínimos.
Prueba selección, vista previa, guardado y persistencia.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 10. Rediseñar Nueva publicación como Instagram (vista previa adaptable)
**Esfuerzo: Medium**

```text
Rediseña "Nueva publicación" de CampusConnect con estilo Instagram y colores UNA.

1. Usa tarjeta blanca con avatar y nombre arriba, campo de texto visible y botón rojo #E4002B.
2. Acepta JPG, JPEG, PNG, WEBP y GIF (primer fotograma).
3. Muestra vista previa grande al seleccionar foto.
4. Ajusta la imagen al espacio disponible, conservando proporción, sin recortes ni deformaciones.
5. Adapta el formulario al tamaño de imagen dentro de límites razonables, sin barras horizontales; si es muy alta, limita vista previa y permite scroll vertical con mouse.
6. Permite cambiar o quitar la imagen al instante.
7. Admite fotos verticales, horizontales y cuadradas.
8. Permite publicar texto, imagen o ambos.
9. Limpia el formulario tras publicar correctamente.
10. Mantén Enter para publicar y Shift+Enter para saltos de línea.
11. Conserva todo integrado en Inicio, sin ventanas adicionales.
12. Reutiliza lógica y persistencia JSON existentes.
13. Muestra imágenes completas también en Inicio, Mi muro y perfiles.

RESTRICCIONES:
- Mantén Python, Tkinter y ttk; Pillow si es necesario.
- Conserva las demás funcionalidades y datos.

AHORRO DE TOKENS:
Revisa solo archivos necesarios y haz cambios mínimos.
Prueba imágenes verticales, horizontales, cuadradas, vista previa y publicación.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 11. Botones de inicio de sesión: Volver arriba a la derecha
**Esfuerzo: Low**

```text
Ajusta la pantalla de inicio de sesión de CampusConnect para que tenga exactamente esta distribución:

1. Botón "Volver" pequeño, arriba a la derecha, con flecha hacia la izquierda.
2. Icono de CampusConnect centrado arriba.
3. Título "Iniciar sesión" centrado.
4. Campos de usuario y contraseña alineados, del mismo ancho y con bordes suaves.
5. Botones "Iniciar sesión" y "Registrarse" uno junto al otro, del mismo ancho y alto.
6. "Iniciar sesión": fondo rojo UNA #E4002B y texto blanco.
7. "Registrarse": fondo blanco, borde rojo y texto rojo.
8. Formulario centrado y adaptable a la ventana.
9. Conserva efectos hover y validaciones.

RESTRICCIONES:
- Modifica únicamente la GUI del login.
- No alteres autenticación ni datos.
- Mantén Python, Tkinter y ttk y reutiliza código existente.

AHORRO DE TOKENS:
Haz cambios mínimos y prueba los tres botones.
Resume resultados en máximo 3 líneas. No hagas commits ni push.
```

## 12. Agregar publicación arriba a la izquierda, foto de perfil y nuevo estilo de reacciones
**Esfuerzo: Medium**

```text
Mejora tres elementos de CampusConnect con estilo moderno tipo Instagram y colores UNA.

1. FOTO DE PERFIL
- Permite seleccionar foto desde Editar perfil.
- Muestra vista previa circular antes de guardar, respetando recorte y centrado final.
- Agrega Guardar foto, Cambiar foto y Cancelar.
- Acepta JPG, JPEG, PNG, WEBP y GIF.
- Actualiza avatar en perfiles, buscador, amigos, publicaciones y respuestas.
- Conserva iniciales si no existe foto.

2. AGREGAR PUBLICACIÓN
- Quita formulario permanente de Inicio y texto "¿Qué está pasando?".
- Agrega "+ Agregar publicación" arriba a la izquierda del área principal.
- Al pulsarlo muestra formulario dentro de la misma ventana.
- Permite texto, imagen o ambos, con vista previa, cambiar, quitar, Publicar y Cancelar.
- Conserva Enter para publicar y Shift+Enter para saltos de línea.
- Al publicar, actualiza Inicio; al cancelar, descarta el borrador y vuelve al feed.

3. REACCIONES
- Rediseña: Me gusta, Me divierte y No me gusta.
- Usa iconos, texto y contadores individuales; destaca seleccionada con rojo UNA.
- Mantén botones compactos y alineados; permite cambiar o quitar reacción.
- Aplica el mismo diseño en Inicio, Mi muro y perfiles.

RESTRICCIONES:
- Mantén Python, Tkinter, ttk y JSON; usa Pillow si existe.
- Una sola ventana, reutiliza componentes y gestores.
- No elimines datos ni modifiques otras funciones.

AHORRO DE TOKENS:
Revisa solo archivos necesarios, haz cambios mínimos y prueba persistencia.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 13. Mostrar solo @usuario y permitir hilos anidados con imágenes
**Esfuerzo: High (o Medium inicialmente para ahorrar)**

```text
Mejora CampusConnect con hilos similares a X (Twitter).

1. Muestra únicamente @usuario en publicaciones, respuestas, perfiles, buscador y amigos; conserva nombres internamente.
2. Permite responder a publicaciones y también a otras respuestas.
3. Cada respuesta guarda ID, autor, fecha, texto, imagen opcional y referencia al padre.
4. Muestra conversaciones encadenadas con líneas verticales y sangrías moderadas.
5. Indica claramente a qué @usuario se responde.
6. Permite responder con texto, imagen o ambos, con vista previa antes de enviar.
7. Acepta JPG, JPEG, PNG, WEBP y GIF (primer fotograma).
8. Conserva proporciones y guarda imágenes con rutas relativas.
9. Permite expandir/contraer respuestas; para hilos profundos, usa vista de conversación.
10. Mantén diseño uniforme en Inicio, Mi muro y perfiles y navegación interna.
11. Conserva las reacciones existentes: Me gusta, Me divierte y No me gusta.
12. Actualiza hilos automáticamente y conserva recarga manual.
13. Mantén compatibilidad con publicaciones y comentarios antiguos JSON.

RESTRICCIONES:
- Reutiliza modelos, gestores y GUI existentes.
- Python, Tkinter, ttk, Pillow si existe y JSON; estética UNA y una sola ventana.
- No cambies autenticación ni amistades; no agregues mensajería/notificaciones en esta tarea.
- No elimines datos.

AHORRO DE TOKENS:
Revisa solo archivos relacionados, haz cambios puntuales y prueba hilos, imágenes y persistencia.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 14. Modo oscuro y claro con colores UNA
**Esfuerzo: Medium**

```text
Agrega modo claro y oscuro a CampusConnect, manteniendo colores UNA.

1. Conserva el modo claro actual.
2. Crea modo oscuro con fondo #111318, tarjetas #1E2128, rojo #E4002B, texto #F9FAFB, texto secundario #AEB4C0 y bordes #343943.
3. Agrega botón sol/luna para cambiar tema inmediatamente sin reiniciar.
4. Aplica los temas a registro, login, Inicio, amigos, buscador, perfiles, publicaciones, comentarios, hilos y reacciones.
5. Centraliza colores en un sistema reutilizable.
6. Garantiza buen contraste en textos, campos, botones, scroll, hover y elementos seleccionados.
7. Utiliza rojo UNA como acento.
8. Conserva sección actual y borradores al cambiar tema.
9. Guarda preferencia en JSON de configuración separado; restáurala al abrir.
10. Mantén todas las funciones existentes.

RESTRICCIONES:
- Python, Tkinter, ttk y JSON, sin dependencias nuevas.
- No cambies lógica, datos ni otras fases.
- Conserva navegación en una sola ventana.

AHORRO DE TOKENS:
Revisa solo archivos necesarios; reutiliza componentes y evita refactorizaciones.
Prueba ambos temas y persistencia. Resume resultados en máximo 5 líneas.
No hagas commits ni push.
```

## 15. Login directo, sin ventana emergente de éxito
**Esfuerzo: Low**

```text
Mejora el inicio de sesión de CampusConnect.

1. Si usuario y contraseña son correctos, inicia sesión inmediatamente y abre Inicio.
2. Elimina la ventana emergente de confirmación de inicio de sesión exitoso.
3. Conserva mensajes de error para credenciales incorrectas o campos vacíos.
4. Mantén login con Enter y con el botón.
5. Evita abrir panel principal más de una vez.
6. Conserva sesión y navegación existentes.

RESTRICCIONES:
- Modifica solo flujo de éxito del login.
- No cambies autenticación, validaciones ni JSON.
- Mantén Python y Tkinter sin dependencias nuevas.

AHORRO DE TOKENS:
Revisa solo archivos necesarios; prueba login correcto e incorrecto.
Resume resultados en máximo 3 líneas. No hagas commits ni push.
```

## 16. Ocultar barras de scroll, botón recargar como icono, ver respuestas y responder como Instagram
**Esfuerzo: Medium**

```text
Mejora interfaz de publicaciones de CampusConnect con estilo Instagram/X.

1. Oculta barras de scroll visibles en Inicio, Mi muro, perfiles y respuestas, manteniendo rueda del mouse sobre tarjetas, imágenes y textos.
2. Evita desplazamientos duplicados o que afecten otras vistas.
3. Cambia botón "Actualizar" por icono pequeño circular de recarga, sin texto, conservando funcionalidad.
4. Muestra "Ver respuestas" únicamente cuando haya una o más; si hay contador, usa por ejemplo "Ver 3 respuestas".
5. Si no hay respuestas, no muestres enlace ni espacio vacío.
6. Rediseña la acción Responder como botón/icono compacto estilo Instagram.
7. Al pulsarlo abre respuesta dentro de la misma publicación, sin nuevas ventanas.
8. Conserva texto e imágenes en respuestas si ya están implementados.
9. Mantén estética UNA, tarjetas limpias y acciones consistentes.

RESTRICCIONES:
- Python, Tkinter, ttk; sin dependencias nuevas innecesarias.
- Reutiliza GUI y lógica; una sola ventana, sin cambios de negocio ajenos al alcance.

AHORRO DE TOKENS:
Revisa solo GUI relacionada, haz cambios mínimos y prueba scroll, recarga y respuestas.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 17. Editor para acomodar y recortar la foto de perfil
**Esfuerzo: Medium**

```text
Mejora edición de fotos de perfil de CampusConnect con editor visual similar a Instagram.

1. Al seleccionar foto, muestra editor dentro de la misma ventana.
2. Muestra vista previa circular que represente exactamente el avatar final.
3. Permite arrastrar foto con mouse horizontal y verticalmente.
4. Agrega slider para acercar/alejar imagen.
5. Permite rueda del mouse para zoom únicamente sobre editor, sin desplazar página.
6. Agrega Restablecer, Cancelar y Guardar foto.
7. Restablecer centra imagen automáticamente.
8. Cancelar conserva foto anterior.
9. Guardar genera recorte elegido usando Pillow.
10. Actualiza avatar en perfiles, buscador, amigos, publicaciones y respuestas.
11. Acepta JPG, JPEG, PNG, WEBP y GIF.
12. Admite fotos verticales, horizontales y cuadradas sin deformaciones ni espacios vacíos.
13. Mantén vista previa fluida y precisa.

RESTRICCIONES:
- Mantén Python, Tkinter, ttk, Pillow y JSON.
- Reutiliza edición de perfil, una sola ventana y estética UNA.
- No agregues dependencias nuevas ni borres datos.

AHORRO DE TOKENS:
Revisa solo archivos relacionados; prueba arrastre, zoom, cancelar, guardar y persistencia.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 18. Quitar fondos y bordes blancos de iconos y avatares
**Esfuerzo: Low**

```text
Corrige detalles visuales de iconos y fotos de perfil en CampusConnect.

1. Elimina fondos blancos o diferentes detrás de iconos. Usa transparencia cuando sea posible o el color exacto del contenedor.
2. Aplica a navegación, publicaciones, reacciones, respuestas, actualizar y perfiles.
3. Elimina bordes, halos y márgenes blancos alrededor de fotos circulares.
4. Haz que las fotos ocupen el avatar sin espacios blancos ni deformaciones.
5. Si proviene de Pillow, corrige máscara circular y canal alfa para bordes suaves transparentes.
6. Si viene de Canvas, Label o widgets Tkinter, iguala fondo al contenedor.
7. Aplica en Inicio, perfiles, amigos, buscador, publicaciones y respuestas.
8. Garantiza modo claro/oscuro al cambiar tema.
9. Conserva hover y selección sin fondos blancos no deseados.

RESTRICCIONES:
- Python, Tkinter, ttk, Pillow, JSON.
- No cambies lógica ni datos; conserva encuadres; sin dependencias nuevas.

AHORRO DE TOKENS:
Revisa solo archivos necesarios, aplica cambios mínimos y verifica ambos temas.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 19. Publicaciones: tiempo relativo y fecha
**Esfuerzo: Low**

```text
Simplifica fechas de publicaciones de CampusConnect.

1. Debajo de @usuario muestra únicamente: "Hace 5 minutos · 14/11/2026".
2. Calcula tiempo desde fecha/hora real de creación.
3. Usa segundos, minutos, horas o días según corresponda.
4. Fecha DD/MM/AAAA sin hora exacta.
5. Elimina indicadores temporales redundantes.
6. Aplica en Inicio, Mi muro y perfiles.
7. Actualiza al recargar y maneja fechas inválidas sin errores.
8. Conserva @usuario, imágenes, reacciones, respuestas y orden.

RESTRICCIONES:
- Modifica solo presentación de fechas; Python, Tkinter, ttk y JSON.
- No cambies fechas almacenadas ni ordenamiento.

AHORRO DE TOKENS:
Revisa solo archivos necesarios, haz cambios mínimos y prueba fechas recientes/antiguas.
Resume resultados en máximo 3 líneas. No hagas commits ni push.
```

## 20. Eliminar publicaciones propias
**Esfuerzo: Low**

```text
Agrega opción de eliminar publicaciones propias a CampusConnect.

1. Muestra menú de tres puntos (...) en cada publicación.
2. Muestra "Eliminar publicación" únicamente al autor original.
3. Solicita confirmación antes de eliminar.
4. Verifica permisos también en GestorPublicaciones, no solo interfaz.
5. Elimina publicación de publicaciones.json y actualiza Inicio, Mi muro y perfiles sin reiniciar.
6. Elimina o actualiza consistentemente respuestas, reacciones y reposts relacionados.
7. No borres imágenes utilizadas por otros contenidos.
8. Si usuario cancela, conserva todo.
9. Prueba eliminación propia, intento ajeno, cancelación y persistencia.

RESTRICCIONES:
- Reutiliza clases y gestores existentes; Python, Tkinter, ttk y JSON.
- No borres información no relacionada; estética UNA y una sola ventana.

AHORRO DE TOKENS:
Revisa solo archivos necesarios, haz cambios mínimos y ejecuta pruebas.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 21. Repostear publicaciones
**Esfuerzo: Medium**

```text
Agrega reposts a CampusConnect, similares a X.

1. Agrega botón con icono de repost debajo de cada publicación.
2. Permite repostear publicaciones ajenas sin duplicar contenido.
3. Muestra "@usuario reposteó" encima del contenido.
4. Conserva autor, texto, imágenes, fecha, respuestas y reacciones originales.
5. Muestra repost en Mi perfil y en Inicio de mis amigos, ordenado por fecha del repost.
6. Evita repost doble del mismo usuario a la misma publicación.
7. Permite deshacer repost propio sin eliminar original.
8. Muestra contador de reposts.
9. Permite abrir perfiles del autor original y quien reposteó.
10. Guarda reposts mediante referencias al ID original en JSON, sin duplicar contenido.
11. Maneja eliminación del original y reposts asociados.
12. Mantén compatibilidad con publicaciones antiguas.
13. Prueba repost, duplicados, persistencia y deshacer.

RESTRICCIONES:
- Reutiliza GestorPublicaciones y GUI; Python, Tkinter, ttk y JSON.
- Conserva reacciones, hilos, imágenes y estética UNA.
- No agregues notificaciones ni dependencias nuevas.

AHORRO DE TOKENS:
Revisa solo archivos relacionados y haz cambios mínimos.
Ejecuta pruebas relevantes. Resume resultados en máximo 5 líneas.
No hagas commits ni push.
```

## 22. Chat privado entre amigos
**Esfuerzo: Medium**

```text
Agrega chat privado entre amigos a CampusConnect, similar a mensajes directos de Instagram.

1. Agrega "Mensajes" al menú lateral.
2. Muestra conversaciones con avatar, @usuario, último mensaje y fecha.
3. Permite abrir chats desde Amigos y perfiles.
4. Solo permite conversar entre usuarios amigos, validado también en gestor.
5. Implementa chats individuales, no grupales.
6. Muestra mensajes propios a derecha en rojo UNA y recibidos a izquierda.
7. Enter envía y Shift+Enter inserta salto de línea.
8. Ordena mensajes del más antiguo al más reciente.
9. Guarda remitente, destinatario, fecha, contenido, ID y estado de lectura.
10. Conserva conversaciones al reiniciar.
11. Actualiza chat al enviar.
12. Agrega recarga manual y contador de no leídos.
13. Permite scroll con mouse sin barras visibles.
14. Muestra solo @usuario, no nombres completos.
15. Mantén modo claro, oscuro y estética UNA.

RESTRICCIONES:
- Reutiliza usuarios, sesiones y amistades existentes.
- Mantén Python, Tkinter, ttk y JSON; sin dependencias externas.
- No afectes publicaciones, perfiles ni reacciones.
- No simules mensajería en tiempo real entre computadoras.
- Guarda mensajes localmente fuera de Git mediante .gitignore; no publiques chats privados.

AHORRO DE TOKENS:
Revisa solo archivos necesarios; prueba mensajes, persistencia y permisos.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 23. Enviar fotos por chat
**Esfuerzo: Medium**

```text
Agrega envío de imágenes al chat de CampusConnect.

1. Agrega botón para adjuntar imágenes.
2. Acepta JPG, JPEG, PNG, WEBP y GIF.
3. Permite enviar imagen sola o acompañada de texto.
4. Muestra vista previa antes de enviar.
5. Permite cambiar, quitar o cancelar imagen.
6. Muestra imágenes en burbujas sin deformarlas.
7. Permite ampliarlas dentro de la misma ventana.
8. Guarda imágenes localmente con rutas relativas y nombres únicos.
9. Valida archivos y tamaño máximo de 10 MB.
10. Actualiza chat al enviar.
11. Mantén compatibilidad con mensajes anteriores.

RESTRICCIONES:
- Reutiliza Pillow y gestores existentes.
- Mantén Python, Tkinter, ttk y JSON.
- No compartas mensajes ni fotos privadas por Git.
- No agregues dependencias innecesarias.

AHORRO DE TOKENS:
Revisa solo archivos del chat necesarios, haz cambios mínimos y prueba persistencia.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 24. Iconos de publicación limpios, compartir a chat y mensajes como Instagram
**Esfuerzo: Medium**

```text
Mejora CampusConnect: acciones de publicaciones limpias y Mensajes estilo Instagram.

A. ACCIONES DE PUBLICACIÓN
1. Muestra Me gusta solo como corazón, sin texto.
2. Quita cuadros y fondos rojos de iconos; iguala fondo al contenedor.
3. Al estar activa una acción, pinta solo el icono en rojo UNA #E4002B; en reposo color neutro.
4. Conserva contadores discretos fuera de cajas rojas.
5. Elimina acción "Me divierte" y sustitúyela por Compartir/Enviar a chat.
6. Permite compartir publicación a uno o varios amigos.
7. Conserva repost si existe, con estilo limpio.
8. Alinea acciones en una fila consistente.

B. COMPARTIR A CHAT
9. Abre selector de amigos y chats recientes dentro de la misma ventana.
10. Envía publicación como referencia con autor, texto e imagen.
11. Si existe chat úsalo; si no, créalo.

C. MENSAJES
12. Dos columnas: izquierda conversaciones/amigos; derecha chat activo.
13. A la izquierda muestra avatar, @usuario y último mensaje; permite ver amigos sin chat previo.
14. Agrega búsqueda de amigos/chats.
15. Seleccionar amigo abre o inicia chat.
16. Mensajes propios a derecha, recibidos a izquierda.
17. Scroll con mouse, sin barra visible.
18. Mejora campo de escritura, adjuntar imagen y botón enviar.
19. Muestra solo @usuario; estado vacío cuando no hay chat.

D. DISEÑO Y RESTRICCIONES
20. Mantén estética UNA, modos claro/oscuro, una sola ventana, hover sutil.
21. Python, Tkinter, ttk; reutiliza chats, reacciones, amistades y publicaciones.
22. No cambies autenticación ni borres datos; no agregues dependencias innecesarias.

AHORRO DE TOKENS:
Revisa solo archivos de publicaciones, reacciones, compartir y mensajes.
Haz cambios mínimos y prueba compartir, lista de amigos, inicio de chat e iconos.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 25. Separadores, lupa y acciones a la derecha de publicaciones
**Esfuerzo: Medium (Low si es solo acomodo visual)**

```text
Mejora interfaz de CampusConnect en Mensajes y publicaciones.

A. MENSAJES
1. Agrega líneas de separación entre barra de búsqueda y lista, entre cada chat y entre columna izquierda y conversación.
2. Usa separadores sutiles que funcionen en modo oscuro y claro.
3. Agrega icono de lupa a la izquierda de la barra de búsqueda.
4. Mantén búsqueda funcional y alineada.
5. Organiza lista izquierda como chats de Instagram.

B. PUBLICACIONES
6. Mueve iconos de Me gusta, Compartir, Repostear y demás acciones al lado derecho de cada tarjeta, no debajo.
7. Alinea iconos verticalmente en columna derecha.
8. Mantén estilo sin cuadros rojos.
9. Cuando acción esté activa, pinta solo icono de rojo #E4002B.
10. Conserva contadores discretos y alineados.
11. No pongas acciones debajo del texto o imagen.

C. RESTRICCIONES
- Mantén modo claro/oscuro, estética UNA y una sola ventana.
- Python, Tkinter, ttk; reutiliza GUI y lógica.
- No cambies lógica fuera de lo necesario ni borres datos.

AHORRO DE TOKENS:
Revisa solo archivos de Mensajes y publicaciones; haz cambios mínimos.
Prueba separadores, buscador y acciones.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 26. Rediseño específico de Mensajes como Instagram
**Esfuerzo: Medium**

```text
Rediseña únicamente Mensajes de CampusConnect con estilo Instagram en escritorio y colores UNA.

1. Usa dos columnas: izquierda 30-35% para conversaciones y amigos; derecha para conversación activa.
2. Agrega línea vertical entre columnas y separadores horizontales entre conversaciones.
3. Incluye buscador con icono de lupa.
4. Cada conversación muestra avatar, @usuario, último mensaje y fecha discreta.
5. Resalta conversación seleccionada.
6. Permite abrir chats con cualquier amigo aunque no existan mensajes.
7. Agrega encabezado fijo con avatar y @usuario; permite abrir perfil.
8. Muestra mensajes propios a derecha en rojo UNA y recibidos a izquierda en gris.
9. Mantén cuadro de escritura fijo abajo, con adjuntar imagen y enviar.
10. Enter envía; Shift+Enter agrega salto de línea.
11. Al abrir chat desplázate al mensaje más reciente; oculta barras de scroll, conserva rueda.
12. Sin chat seleccionado, muestra mensaje centrado para elegir amigo.
13. Muestra publicaciones compartidas como tarjetas compactas que abren el original.
14. Conserva modos claro/oscuro y diseño UNA.
15. Reutiliza gestores, mensajes y datos existentes.

RESTRICCIONES:
- Mantén Python, Tkinter, ttk y Pillow si existe.
- No agregues dependencias nuevas, no abras ventanas ni borres datos.
- No cambies lógica fuera de lo necesario.

AHORRO DE TOKENS:
Revisa solo archivos relacionados con Mensajes, realiza cambios mínimos y prueba búsqueda, selección, envío, imágenes, navegación y ambos temas.
Resume resultados en máximo 5 líneas. No hagas commits ni push.
```

## 27. Complemento del último: acciones a la derecha
**Esfuerzo: Low**

```text
Mejora únicamente las acciones de las publicaciones.

1. Mueve iconos de Me gusta, Compartir, Repostear y demás acciones existentes a la parte derecha de cada publicación.
2. Organízalos verticalmente y bien alineados.
3. Elimina cuadros y fondos rojos.
4. Mantén únicamente iconos y contadores.
5. Cuando una acción esté activa, pinta solo el icono en rojo UNA #E4002B.
6. Conserva diseño en modo claro y oscuro.
7. Aplica cambios en Inicio, Mi muro y perfiles.

No modifiques lógica ni otras funcionalidades.
Reutiliza componentes, realiza cambios mínimos y verifica botones.
Resume resultados en máximo 3 líneas.
No hagas commits ni push.
```

---

### Nota sobre cambios sucesivos
Estos prompts reproducen las solicitudes sucesivas de la conversación y **no todos se deben aplicar al mismo tiempo**. Algunos se reemplazan por otros posteriores: por ejemplo, primero se solicitó «Me divierte», pero más adelante se pidió quitarlo y sustituirlo por compartir al chat. Si vas a partir del código actual, prioriza los prompts finales que correspondan al diseño vigente.