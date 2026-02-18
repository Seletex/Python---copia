# Plan de Despliegue en Render

Este plan detalla los pasos finales para subir la aplicación a Render de manera correcta, aprovechando los cambios técnicos que ya hemos realizado.

## Paso 1: Preparación del Repositorio (Git)

Para subir a Render, el código debe estar en un repositorio (GitHub o GitLab).

1. **Inicializar Git** (si no se ha hecho): `git init` dentro de la carpeta `Actividades`.
2. **Agregar archivos**: Asegurarse de incluir `app.py`, `render.yaml`, `requirements.txt`, la carpeta `templates` y los archivos de Excel (**que acabo de copiar dentro de esta carpeta para ti**).
3. **Commit**: `git add .` y `git commit -m "Preparación para despliegue en Render"`.
4. **Push**: Subir a un repositorio remoto en GitHub.

## Paso 2: Configuración en Render

Utilizaremos el archivo `render.yaml` que ya creamos para automatizar todo.

1. Ir al Dashboard de **Render**.
2. Hacer clic en **"Blueprints"**.
3. Seleccionar **"Connect a repository"** y elegir el repositorio de GitHub.
4. Render detectará automáticamente el archivo `render.yaml` y creará:
   - El servicio web (Flask + Gunicorn).
   - La base de datos PostgreSQL.
   - Las variables de entorno necesarias (`DATABASE_URL`, `SECRET_KEY`).

## Paso 3: Verificación Post-Despliegue

1. Acceder a la URL que proporcione Render.
2. Iniciar sesión (el usuario `admin` se creará automáticamente).
3. Probar la creación de un registro y la exportación a Excel para confirmar que las rutas de las plantillas son correctas.

> [!IMPORTANT]
> **Persistencia**: Al usar el Blueprint con PostgreSQL, tus datos estarán seguros y no se borrarán al reiniciar el servidor.

> [!WARNING]
> Asegúrate de que el archivo `.gitignore` incluya archivos sensibles como `actividades.db` o `usuarios.json` de tu entorno local para no sobreescribir los datos de producción.
