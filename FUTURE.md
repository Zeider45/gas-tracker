# Mejoras Futuras (Roadmap)

Esta lista recopila ideas para evolucionar Gas Tracker más allá del MVP actual.

## Funcionalidad

- Perfil de vehículo: capacidad de tanque, eficiencia base, tipo de combustible.
- Múltiples vehículos por usuario y selección activa.
- Modo offline: almacenar puntos en IndexedDB y sincronizar al reconectar.
- Reanudación automática de viaje tras cierre accidental de la app.
- Mapas interactivos: polilínea del trayecto, markers de inicio/fin, heatmap de uso.
- Detección de paradas (clustering temporal) y segmentación dentro de un viaje.
- Exportar datos: CSV/JSON/GPX y compartir viaje.
- Historial avanzado: filtros por fecha, distancia, consumo.
- Notificaciones push (Web Push) para recordatorio de snapshot de combustible o baja autonomía.
- Unidades configurables (millas, galones) y conversión automática.
- Integración con sensores OBD-II (si se expande a móvil nativo) para lectura real de combustible.

## Rendimiento y Precisión

- Smoothing de trayectoria (Douglas-Peucker) para reducir ruido.
- Ajuste a caminos reales mediante API de mapas (map matching).
- Cálculo de consumo por condiciones (urbano vs carretera) con clustering.

## Seguridad

- Rotación del JWT y refresh tokens.
- Rate limiting básico para endpoints sensibles.
- Encriptación opcional de base de datos local (SQLite + extensión).

## Arquitectura

- Migrar a Prisma para esquema tipado y migraciones.
- Separar servicios (auth, trips, fuel) en módulos internos con tests dedicados.
- Añadir capa de repositorio y DTOs para facilitar futura migración a otra DB.

## UI/UX

- Indicador de calidad de señal GPS.
- Modo oscuro/claro automático.
- Panel de comparación entre vehículos.
- Dashboard con gráficas (consumo vs tiempo, distancia diaria).

## PWA / Mobile

- Background sync para enviar puntos mientras la app está en segundo plano (Workbox + Background Sync API).
- Instalación guiada con pantalla de onboarding.
- Generación de íconos automáticos y splash screens.

## DevOps

- Dockerización (multi-stage build para backend, nginx para servir frontend).
- Pipeline CI (lint, test, build) + badges.
- Análisis de cobertura de tests y reporte.

## Tests

- Tests de rutas con supertest y mocks para DB.
- Tests de geolocalización simulada (mock de navigator.geolocation).

## Internacionalización

- i18n con soporte para inglés/español y ampliación futura.

## Monetización (opcional)

- Plan premium: histórico extendido, múltiples vehículos, exportaciones avanzadas.
- Integración de ads limitada o patrocinios.

## Próximos pasos sugeridos

1. Integrar mapa con Leaflet para mostrar puntos en tiempo real.
2. Añadir background sync y cola offline de puntos.
3. Ampliar cobertura de tests (rutas + cálculo de proyecciones con casos edge).
4. Refactor a repositorios y servicios testeables.
5. Añadir exportación CSV de viajes.

---

Contribuciones: abrir issues indicando la sección y la propuesta concreta.
