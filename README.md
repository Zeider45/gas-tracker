# Gas Tracker

Aplicación web (backend Express + SQLite y frontend React + Vite PWA) para rastrear recorridos y consumo de gasolina.

## Características

- Registro e inicio de sesión con JWT.
- Inicio y fin de viajes, puntos geolocalizados cada 5s (manual mediante botón de seguimiento).
- Cálculo de distancia usando fórmula Haversine.
- Snapshots de combustible y estadísticas: consumo medio (L/100km), rango proyectado, días restantes.
- PWA instalable (manifest + service worker cache simple).

## Estructura

```
server/  -> API Express + SQLite
client/  -> Frontend React + Vite
```

## Requisitos

- Node.js 18+ (probado con versión actual).
- Windows PowerShell (entorno actual) o cualquier shell.

## Configuración Backend

1. Copiar `.env.example` a `.env` y ajustar:

```
PORT=4000
JWT_SECRET=tu-secreto
DB_PATH=./data/gastracker.db
```

2. Instalar dependencias:

```powershell
cd server
npm install
```

3. Ejecutar en desarrollo:

```powershell
npm run dev
```

## Configuración Frontend

1. Copiar `client/.env.example` a `client/.env` si deseas cambiar la URL:

```
VITE_API_BASE=http://localhost:4000
```

2. Instalar dependencias y ejecutar:

```powershell
cd client
npm install
npm run dev
```

3. Abrir http://localhost:5173 y usar la app.

### Acceso desde el móvil (misma red LAN)

Para ver la app en tu celular mientras desarrollas:

1. Asegúrate de que el backend escuche en todas las interfaces (`HOST=0.0.0.0` por defecto en código) y que el frontend Vite tenga `host: true` (ya configurado).
2. Obtén la IP local de tu PC (ejemplo `192.168.1.50`). En PowerShell:
   ```powershell
   ipconfig | findstr /R /C:"IPv4"
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

Notas:

- Si no carga, revisa firewall de Windows: permite conexión entrante a Node/Vite en puertos 4000 y 5173.
- Cambia la IP en `.env` si tu red asigna otra al reiniciar.
- Para producción, usa un dominio/HTTPS y configura correctamente CORS si separas hostnames.

## Flujo de Uso

1. Crear cuenta / iniciar sesión.
2. (Opcional) Registrar snapshot de combustible inicial.
3. Iniciar viaje.
4. Activar seguimiento (botón "Comenzar seguimiento"). Cada ~5s envía posición.
5. Finalizar viaje.
6. Registrar nuevo snapshot de combustible para mejorar estadísticas.

## PWA

- Manifest en `client/public/manifest.json`.
- Service Worker básico en `client/src/service-worker.ts` (cache "app shell" y fetch network-first luego cachea).
- Registro en `client/src/pwa.ts`.

Para producción, tras `npm run build` en client, servir carpeta `client/dist` detrás de un servidor estático.

## Tests

Pruebas unitarias con Vitest en `server/src/tests`:

- `calc.test.ts`: distancia Haversine y estadísticas de consumo.

Ejecutar:

```powershell
cd server
npm test
```

## Mejoras Futuras

Ver el roadmap detallado en `FUTURE.md`. Resumen clave:

- Multi vehículo.
- Offline y sincronización.
- Mapas del recorrido.
- Exportaciones y analítica.
- Edición/eliminación de viajes.

## Seguridad / Consideraciones

- JWT expira a los 7 días (re-login luego).
- Falta rate limiting y protección CSRF (no crítico para API solo token).
- No se cifra la base de datos local.

## Troubleshooting

- Si `better-sqlite3` falla en Windows, ya se reemplazó por `sqlite3` para evitar compilación nativa.
- Verifica que la ubicación devuelva coordenadas (en desktop puede requerir permisos del navegador).

## Scripts

Backend:

- `npm run dev` desarrollo con recarga.
- `npm run build` compila TypeScript.
- `npm start` ejecuta build.

Frontend:

- `npm run dev` servidor Vite.
- `npm run build` empaqueta.
- `npm run preview` vista previa producción.

## Licencia

Uso interno / educativo.
