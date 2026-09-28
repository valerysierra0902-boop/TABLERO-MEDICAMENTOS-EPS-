# Tablero de medicamentos dispensados 2020-2021

Proyecto en **Python + Dash + SQL (SQLite)**.

## Ejecutar localmente

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

Abrir `http://127.0.0.1:8050`.

## Despliegue en Render

1. Subir esta carpeta a un repositorio de GitHub, incluyendo `medicamentos.db`.
2. En Render: **New > Web Service** y conectar el repositorio.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:server`
5. Desplegar y copiar la URL pública que genera Render.

> La base SQLite se usa en modo lectura. Para este taller es suficiente porque el archivo se distribuye junto al código.

## Nota de calidad de datos

En 2020, `grupo_fco_economico` está vacío en todos los registros. Por eso el análisis de ANTIDIABÉTICOS clasificado directamente solo existe en 2021. La comparación 2020-2021 del informe se construye como aproximación: se toman los nombres de medicamentos clasificados como ANTIDIABÉTICOS en 2021 y se buscan esas mismas descripciones en 2020.
