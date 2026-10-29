# Avivamiento Mexicano

Aplicación Flask para el registro del congreso y la administración de asistentes.

## Ejecutar localmente

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export FLASK_SECRET_KEY="una-clave-larga-y-privada"
.venv/bin/python app.py
```

Abre `http://127.0.0.1:5000` para el sitio público y `/registro` para el formulario. La URL administrativa es `/admin`.

La primera vez que visites `/admin`, la aplicación te pedirá crear el usuario y la contraseña desde una pantalla gráfica. Después podrás entrar desde `/admin/login`.

## Persistencia

Los registros se almacenan en `datos.json` como solución local para desarrollo. Para producción conviene cambiar esta capa por Supabase/PostgreSQL y añadir protección anti-spam.