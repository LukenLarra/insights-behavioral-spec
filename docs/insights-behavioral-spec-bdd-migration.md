# BDD Framework Migration — insights-behavioral-spec

## Contexto

Este documento describe los cambios realizados en `insights-behavioral-spec` para soportar la ejecución de tests BDD a través de la GitHub Action **`shepherd_bdd`**, eliminando la dependencia del contenedor Docker y los scripts `.sh`.

---

## Qué había antes

- Los tests se ejecutaban desde dentro del contenedor `insights-behavioral-spec:latest`, donde los paths eran absolutos y fijos (`/insights-behavioral-spec/`)
- Las variables de entorno las exportaba el `.sh` de cada servicio (por ejemplo `parquet_factory_tests.sh`)
- Los paths a binarios y datos de test estaban hardcodeados en los steps de behave
- No había configuración centralizada por servicio fuera de los `.sh`

---

## Qué hay ahora

### 1. Nueva carpeta `bdd-configs/`

Contiene un fichero `<service>-framework.yml` por servicio, análogo a los `.sh` actuales. Cada fichero tiene tres secciones principales:

- **`project`** — nombre y versión del servicio
- **`ci`** — metadatos para el workflow: repositorio, nombre de servicio, perfil Docker, si compila Go, y opcionalmente un `binary_repo` separado
- **`tests`** — comando behave, paths a features/steps, y variables de entorno

Los paths en la sección `env` son relativos al workspace raíz del runner (donde conviven el repo del servicio e `insights-behavioral-spec` en subcarpeta). El script `resolve_bdd_env_paths.py` los convierte a rutas absolutas antes de ejecutar el framework.

Ejemplo — `bdd-configs/parquet-factory-framework.yml`:

```yaml
project:
    name: "parquet-factory"
    version: "1.0.0"

ci:
    repo: "parquet-factory"
    service: "parquet-factory"
    docker_profile: "test-parquet-factory"
    build_go: true

tests:
    enabled: true
    path: "."
    command: "python -m behave @insights-behavioral-spec/test_list/parquet_factory.txt --junit --junit-directory reports/junit --format pretty"
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

Si el binario del servicio está en un repositorio separado, se usa el campo `binary_repo` en la sección `ci`:

```yaml
ci:
    repo: "dvo-writer"
    service: "dvo-writer"
    build_go: true
    binary_repo: "insights-results-aggregator"
```

### 2. Scripts en `.github/scripts/`

**`generate_matrix.py`** — Se ejecuta en el job `generate-matrix`. Escanea todos los `*-framework.yml` de `bdd-configs/`, extrae los campos `repo`, `service`, `build_go`, `binary_repo` y `docker_profile`, y escribe un JSON de matriz en `$GITHUB_OUTPUT` para que el workflow pueda lanzar un job paralelo por servicio.

**`resolve_bdd_env_paths.py`** — Se ejecuta antes de invocar el framework. Recorre la sección `tests.env` del fichero de configuración del servicio y convierte a rutas absolutas cualquier valor que empiece por `insights-behavioral-spec/`, `./` o `../`. Escribe los valores resueltos en `$GITHUB_ENV` y parchea el fichero de configuración en disco para que el framework reciba las rutas absolutas.

### 3. Flujo del workflow (`.github/workflows/pr-bdd-tests.yml`)

```
generate-matrix
    └─ escanea bdd-configs/ y genera la matriz de servicios
         │
         └─ bdd-tests (un job por servicio)
               ├─ checkout insights-behavioral-spec
               ├─ checkout repo del servicio
               ├─ checkout binary_repo (si aplica)
               ├─ instalar dependencias (kcat, Python, Go)
               ├─ compilar binario del servicio
               ├─ enlazar binario en insights-behavioral-spec/
               ├─ preparar symlinks en bdd-configs/
               ├─ resolve_bdd_env_paths.py  ← convierte paths relativos a absolutos
               └─ LukenLarra/shepherd_bdd/actions/main@main  ← ejecuta behave
         │
         └─ publish-reports
               └─ LukenLarra/shepherd_bdd/actions/publish-reports@main
```

### 4. Modificación de `features/steps/parquet_factory.py`

Las constantes de paths hardcodeados se han convertido en variables de entorno con fallback, para que sean configurables desde el `framework.yml` sin romper la compatibilidad con ejecuciones locales.

```python
# ANTES — paths hardcodeados asumiendo working directory dentro del contenedor
PARQUET_FACTORY_BINARY = "parquet-factory"
DATA_DIRECTORY = "test_data"

# AHORA — configurables via variables de entorno
PARQUET_FACTORY_BINARY = os.environ.get("PARQUET_FACTORY_BIN", "parquet-factory")
DATA_DIRECTORY = os.environ.get("TEST_DATA_DIR", "test_data")
```

---

## Añadir soporte para un nuevo servicio

1. Crear `bdd-configs/<service>-framework.yml` siguiendo la estructura del ejemplo anterior
2. Rellenar la sección `ci` con `repo`, `service`, `build_go` y, si aplica, `binary_repo`
3. En la sección `tests.command`, apuntar al fichero de lista de features con `@insights-behavioral-spec/test_list/<service>.txt`
4. Usar `insights-behavioral-spec/` como prefijo en los paths de `tests.bdd` y en los valores de `tests.env` que apunten a ficheros del repo
5. Añadir todas las variables de entorno que necesiten los steps del servicio
6. Si algún step tiene paths hardcodeados, convertirlos a variables de entorno con fallback (como se hizo con `parquet_factory.py`)
