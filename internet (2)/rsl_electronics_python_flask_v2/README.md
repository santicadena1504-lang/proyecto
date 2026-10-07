# RSL Electronics en Python + Base de Datos + CRUD

Este proyecto mantiene el front original y conserva las rutas de imágenes:
`asets (2)/imagenes (2)/...`

## Incluye
- Flask
- Base de datos SQLite automática
- Preparado para MySQL
- Registro de usuarios
- Login y logout
- CRUD de productos
- Carrito visual en front

## Archivos HTML conservados
- inicio (1).html
- internet(1) (1).html
- registro(4).html

## Cómo ejecutar
```bash
pip install -r requirements.txt
python app.py
```

Abre:
http://127.0.0.1:5000/

## Importante sobre imágenes
Coloca tus imágenes originales dentro de:
`static/asets (2)/imagenes (2)/`


## Cambio realizado
- El login quedó como página independiente: `login.html`
- `inicio (1).html` ahora funciona como portada/landing
- La tienda quedó como ruta principal `/`
