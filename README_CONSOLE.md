# Gas Tracker - Versión Consola

Versión de consola del Gas Tracker que permite rastrear viajes y consumo de combustible sin interfaz web.

## Características

- **Gestión de viajes**: Inicia, finaliza y registra kilómetros manualmente
- **Registro de combustible**: Guarda snapshots de combustible
- **Estadísticas**: Calcula consumo promedio, rango proyectado, días restantes
- **Exportación CSV**: Exporta todos los viajes a formato CSV
- **Base de datos SQLite**: Almacenamiento local persistente
- **Interfaz simple**: Menú interactivo en consola

## Requisitos

- Python 3.7+
- Librerías estándar de Python (incluidas)

## Instalación

No requiere instalación de dependencias adicionales. Solo necesitas Python instalado.

## Uso

### Ejecutar la aplicación

```bash
python gas_tracker_console.py
```

O si tienes permisos de ejecución:

```bash
chmod +x gas_tracker_console.py
./gas_tracker_console.py
```

### Opciones del Menú

```
1. Iniciar nuevo viaje
   - Inicia un nuevo viaje
   - Opcionalmente registra el combustible inicial

2. Agregar kilómetros al viaje activo
   - Agrega kilómetros manualmente al viaje en curso
   - Puedes agregar kilómetros múltiples veces

3. Finalizar viaje activo
   - Finaliza el viaje actual
   - Opcionalmente registra el combustible final

4. Registrar snapshot de combustible
   - Guarda el nivel actual de combustible
   - Útil para calcular estadísticas precisas

5. Ver estadísticas
   - Muestra consumo promedio (L/100km)
   - Km promedio por día
   - Rango proyectado con combustible actual
   - Días restantes estimados

6. Ver historial de viajes
   - Lista todos los viajes registrados
   - Muestra distancia, consumo y fechas

7. Exportar viajes a CSV
   - Exporta todos los viajes a un archivo CSV
   - Por defecto: trips_export.csv

0. Salir
   - Cierra la aplicación
```

## Ejemplo de Flujo de Trabajo

### Registro de un viaje completo

1. **Iniciar viaje**
   ```
   Opción: 1
   Combustible inicial: 50
   ```

2. **Agregar kilómetros** (puedes hacer esto varias veces)
   ```
   Opción: 2
   Kilómetros a agregar: 120.5
   ```

3. **Finalizar viaje**
   ```
   Opción: 3
   Combustible final: 45
   ```

4. **Ver estadísticas**
   ```
   Opción: 5
   ```

### Exportar datos

```
Opción: 7
Nombre del archivo: mis_viajes.csv
```

## Base de Datos

La aplicación crea automáticamente una base de datos SQLite en:
```
./data/gastracker_console.db
```

Esta base de datos almacena:
- Viajes con fechas, distancias y niveles de combustible
- Snapshots de combustible
- Usuario por defecto (console@user.local)

## Formato CSV

El archivo CSV exportado contiene las siguientes columnas:

```csv
id,user_id,started_at,ended_at,initial_fuel_liters,final_fuel_liters,total_distance_km
1,1,2025-12-14 10:30:00,2025-12-14 11:30:00,50.0,45.0,120.5
```

## Diferencias con la versión Web

- **Sin GPS**: Los kilómetros se ingresan manualmente
- **Sin autenticación**: Un solo usuario por defecto
- **Sin interfaz gráfica**: Todo por consola
- **Mantiene**: Cálculos de consumo, estadísticas y exportación CSV

## Cálculos

La aplicación utiliza las mismas fórmulas que la versión web:

- **Consumo promedio**: (Litros consumidos / Distancia) × 100
- **Rango proyectado**: Combustible actual / (Litros por km)
- **Días restantes**: Combustible actual / (Litros por día promedio)

Los cálculos se basan en los últimos 20 viajes con datos completos.

## Troubleshooting

### La aplicación no inicia

Verifica que tienes Python 3.7 o superior:
```bash
python --version
```

### Error de permisos en Windows

Ejecuta desde PowerShell o CMD:
```powershell
python gas_tracker_console.py
```

### Base de datos corrupta

Elimina la base de datos y reinicia:
```bash
rm -rf ./data/gastracker_console.db
```

### Caracteres extraños en consola (Windows)

En CMD, configura UTF-8:
```cmd
chcp 65001
```

## Licencia

Uso interno / educativo.
