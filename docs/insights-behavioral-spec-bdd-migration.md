# BDD Framework Migration — insights-behavioral-spec

## Contexto

Este documento describe los cambios realizados en `insights-behavioral-spec` para soportar la ejecución de tests BDD a través de la GitHub Action **`RedHat-BDD-Framework`**, eliminando la dependencia del contenedor Docker y los scripts `.sh`.

---

## Qué había antes

- Los tests se ejecutaban desde dentro del contenedor `insights-behavioral-spec:latest`, donde los paths eran absolutos y fijos (`/insights-behavioral-spec/`)
- Las variables de entorno las exportaba el `.sh` de cada servicio (por ejemplo `parquet_factory_tests.sh`)
- Los paths a binarios y datos de test estaban hardcodeados en los steps de behave
- No había configuración centralizada por servicio fuera de los `.sh`

---

## Qué hay ahora

### 1. Nueva carpeta `bdd-configs/`

Contiene un fichero `<service>-framework.yml` por servicio, análogo a los `.sh` actuales. Define el comando de ejecución de behave, los paths a features/steps y todas las variables de entorno necesarias para ese servicio.

Los paths en estos ficheros son relativos al workspace raíz del runner, donde conviven el repo del servicio e `insights-behavioral-spec` en subcarpeta.

Ejemplo — `bdd-configs/parquet-factory-framework.yml`:

```yaml
project:
    name: "parquet-factory"
    version: "1.0.0"

tests:
    enabled: true
    path: "."
    command: "python -m behave insights-behavioral-spec/features/parquet-factory --junit --junit-directory reports/junit --format pretty"
    bdd:
        features: "insights-behavioral-spec/features/parquet-factory"
        steps: "insights-behavioral-spec/features/steps"
        environment: "insights-behavioral-spec/features/environment.py"
    env:
        KAFKA_HOST: "localhost"
        KAFKA_PORT: "9092"
        PARQUET_FACTORY__KAFKA_RULES__ADDRESS: "localhost:9092"
        S3_OLDER_MINIO_COMPATIBILITY: "1"
        PARQUET_FACTORY__S3__ENDPOINT: "localhost:9000"
        PARQUET_FACTORY__S3__BUCKET: "test"
        PARQUET_FACTORY__S3__ACCESS_KEY: "test_access_key"
        PARQUET_FACTORY__S3__SECRET_KEY: "test_secret_access_key"
        PARQUET_FACTORY__S3__USE_SSL: "false"
        PARQUET_FACTORY__S3__PREFIX: "fleet_aggregations"
        PARQUET_FACTORY__S3__REGION: "us-east-1"
        PARQUET_FACTORY__METRICS__GATEWAY_URL: "localhost:9091"
        PARQUET_FACTORY_BIN: "./parquet-factory"
        TEST_DATA_DIR: "insights-behavioral-spec/test_data"
```

### 2. Modificación de `features/steps/parquet_factory.py`

Las constantes de paths hardcodeados se han convertido en variables de entorno con fallback, para que sean configurables desde el `framework.yml` sin romper la compatibilidad con ejecuciones locales.

```python
# ANTES — paths hardcodeados asumiendo working directory dentro del contenedor
PARQUET_FACTORY_BINARY = "parquet-factory"
DATA_DIRECTORY = "test_data"

# AHORA — configurables via variables de entorno
PARQUET_FACTORY_BINARY = os.environ.get("PARQUET_FACTORY_BIN", "parquet-factory")
DATA_DIRECTORY = os.environ.get("TEST_DATA_DIR", "test_data")
```

Asegurarse de que `import os` está presente en el archivo.

---

## Añadir soporte para un nuevo servicio

Para que un nuevo servicio pueda ejecutar sus tests BDD a través del framework, es necesario crear su fichero de configuración en `bdd-configs/`:

1. Crear `bdd-configs/<service>-framework.yml` siguiendo la estructura del ejemplo anterior
2. Ajustar los paths a features, steps y datos de test usando `insights-behavioral-spec/` como prefijo
3. Añadir todas las variables de entorno que necesiten los steps del servicio
4. Si algún step tiene paths hardcodeados, convertirlos a variables de entorno con fallback (como se hizo con `parquet_factory.py`)
