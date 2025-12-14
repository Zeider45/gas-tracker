# Gas Tracker

Aplicación web (backend Python/FastAPI + SQLite y frontend React + Vite PWA) para rastrear recorridos y consumo de gasolina.

**¿Buscas la versión de consola?** Ver [README_CONSOLE.md](README_CONSOLE.md) para la versión simplificada que se ejecuta solo por consola.

## Características

- Registro e inicio de sesión con JWT.
- Inicio y fin de viajes, puntos geolocalizados cada 5s (manual mediante botón de seguimiento).
- Cálculo de distancia usando fórmula Haversine.
- Snapshots de combustible y estadísticas: consumo medio (L/100km), rango proyectado, días restantes.
- PWA instalable (manifest + service worker cache simple).

## Estructura

```
server_python/        -> API Python FastAPI + SQLite
client/               -> Frontend React + Vite
server/               -> (Deprecado) API Express + SQLite
gas_tracker_console.py -> Versión consola (standalone)
```

## Requisitos

- Python 3.10+ (para el backend FastAPI)
- Node.js 18+ (para el frontend)
- Windows PowerShell, Linux o macOS

## Configuración Backend (Python FastAPI)

1. Copiar `server_python/.env.example` a `server_python/.env` y ajustar:

```
PORT=4000
HOST=0.0.0.0
JWT_SECRET=tu-secreto
DB_PATH=./data/gastracker.db
```

2. Crear un entorno virtual e instalar dependencias:

```bash
cd server_python
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Ejecutar en desarrollo:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload
```

O simplemente:

```bash
python -m app.main
```

## Configuración Frontend

1. Copiar `client/.env.example` a `client/.env` si deseas cambiar la URL:

```
VITE_API_BASE=http://localhost:4000
```

2. Instalar dependencias y ejecutar:

```bash
cd client
npm install
npm run dev
```

3. Abrir http://localhost:5173 y usar la app.

### Acceso desde el móvil (misma red LAN)

Para ver la app en tu celular mientras desarrollas:

1. Asegúrate de que el backend escuche en todas las interfaces (`HOST=0.0.0.0` por defecto en código) y que el frontend Vite tenga `host: true` (ya configurado).
2. Obtén la IP local de tu PC (ejemplo `192.168.1.50`):
   - En Windows PowerShell:
     ```powershell
     ipconfig | findstr /R /C:"IPv4"
     ```
   - En Linux/macOS:
     ```bash
     hostname -I | awk '{print $1}'
     # o
     ip addr show | grep 'inet ' | grep -v '127.0.0.1'
     ```
3. Crea/edita `client/.env` para apuntar al backend con esa IP:
   ```
   VITE_API_BASE=http://192.168.1.50:4000
   ```
4. Reinicia el servidor de desarrollo del cliente (`npm run dev`).
5. En tu teléfono (conectado al mismo Wi‑Fi) abre el navegador y visita:
   ```
   http://192.168.1.50:5173
   ```
6. Inicia sesión / crea cuenta y prueba viaje + snapshots. La PWA te permitirá instalar (banner de instalación) para usarla a pantalla completa.

**Notas sobre acceso desde otros dispositivos:**

- **CORS está configurado para permitir todas las conexiones** (`allow_origins=["*"]`), lo que permite peticiones desde cualquier dispositivo.
- Si no carga, revisa el firewall de tu sistema: permite conexión entrante en puertos 4000 y 5173.
- Cambia la IP en `.env` si tu red asigna otra al reiniciar.
- Para producción, usa un dominio/HTTPS y configura correctamente CORS si separas hostnames.

## PWA (Progressive Web App)

Para que la opción de "Instalar" aparezca en el navegador:

1. **Requisitos del navegador:**
   - Chrome, Edge, o navegadores basados en Chromium (mejor soporte)
   - Firefox en Android (soporte limitado)
   - Safari en iOS (soporte mediante "Añadir a pantalla de inicio")

2. **Requisitos técnicos (ya configurados):**
   - Manifest válido en `client/public/manifest.json`
   - Iconos de 192x192 y 512x512 píxeles en `client/public/`
   - Service Worker registrado
   - La app debe servirse sobre HTTPS en producción (en desarrollo localhost está permitido)

3. **Troubleshooting PWA:**
   - Abre DevTools (F12) > Application > Manifest para verificar que se carga correctamente
   - En Application > Service Workers verifica que el SW está registrado
   - El banner de instalación puede tardar unos segundos en aparecer
   - En móvil, asegúrate de usar el menú del navegador "Instalar app" o "Añadir a pantalla de inicio"

## Flujo de Uso

1. Crear cuenta / iniciar sesión.
2. (Opcional) Registrar snapshot de combustible inicial.
3. Iniciar viaje.
4. Activar seguimiento (botón "Comenzar seguimiento"). Cada ~5s envía posición.
5. Finalizar viaje.
6. Registrar nuevo snapshot de combustible para mejorar estadísticas.

## Tests

### Backend Python (FastAPI)

Pruebas unitarias con pytest en `server_python/app/tests`:

- `test_calc.py`: distancia Haversine y estadísticas de consumo.

Ejecutar:

```bash
cd server_python
python -m pytest app/tests -v
```

### Backend Node.js (Deprecado)

```bash
cd server
npm test
```

## API Endpoints

El servidor FastAPI expone los siguientes endpoints:

- `GET /health` - Health check
- `POST /auth/signup` - Registro de usuario
- `POST /auth/login` - Inicio de sesión
- `GET /auth/me` - Usuario actual (requiere auth)
- `GET /trips/active` - Viaje activo (requiere auth)
- `POST /trips/start` - Iniciar viaje (requiere auth)
- `POST /trips/point` - Agregar punto GPS (requiere auth)
- `POST /trips/stop` - Finalizar viaje (requiere auth)
- `POST /fuel/snapshot` - Registrar combustible (requiere auth)
- `GET /fuel/stats` - Estadísticas de consumo (requiere auth)

Documentación interactiva disponible en:
- Swagger UI: `http://localhost:4000/docs`
- ReDoc: `http://localhost:4000/redoc`

## Mejoras Futuras

Ver el roadmap detallado en `FUTURE.md`. Resumen clave:

- Multi vehículo.
- Offline y sincronización.
- Mapas del recorrido.
- Exportaciones y analítica.
- Edición/eliminación de viajes.

## Seguridad / Consideraciones

- JWT expira a los 7 días (re-login luego).
- CORS permite todas las conexiones para facilitar desarrollo (ajustar en producción).
- Falta rate limiting y protección CSRF (no crítico para API solo token).
- No se cifra la base de datos local.

## Troubleshooting

- **PWA no muestra opción de instalar:** Verifica que los iconos existen en `/client/public/` y que el manifest se carga correctamente.
- **No puedo hacer peticiones desde otro dispositivo:** Asegúrate de usar la IP de red local (no localhost) en `VITE_API_BASE` y verifica el firewall.
- **El servidor no es accesible:** Verifica que `HOST=0.0.0.0` en el backend para escuchar en todas las interfaces.
- Verifica que la ubicación devuelva coordenadas (en desktop puede requerir permisos del navegador).

## Scripts

### Backend Python:

- `python -m uvicorn app.main:app --reload` - desarrollo con recarga
- `python -m uvicorn app.main:app` - producción
- `python -m pytest app/tests -v` - ejecutar tests

### Frontend:

- `npm run dev` - servidor Vite
- `npm run build` - empaqueta
- `npm run preview` - vista previa producción

## Licencia

Uso interno / educativo.
