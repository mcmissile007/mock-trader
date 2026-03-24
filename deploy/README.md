# Deploy Mock Trader — Ubuntu 24 + Docker

## Requisitos

- Ubuntu 24.04 LTS
- Docker Engine ≥ 24.0
- Docker Compose v2 (incluido con Docker Engine)

## Instalación rápida de Docker (Ubuntu 24)

```bash
# Instalar Docker
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Añadir tu usuario al grupo docker (evita usar sudo)
sudo usermod -aG docker $USER
newgrp docker
```

## Despliegue

### 1. Clonar el repositorio

```bash
git clone https://github.com/mcmissile007/mock-trader.git
cd mock-trader
```

### 2. Configurar variables de entorno

```bash
cp deploy/.env.example deploy/.env
# Editar deploy/.env si necesitas cambiar contraseñas u otros valores
nano deploy/.env
```

### 3. Colocar modelos (opcional)

Si usas el trader XGBoost, copia los modelos entrenados:

```bash
mkdir -p data/models/xgboost_v1
cp /ruta/a/tus/modelos/*.joblib data/models/xgboost_v1/
```

### 4. Levantar todo

```bash
cd deploy
docker compose up -d
```

Esto arranca:
- **PostgreSQL 17** con el schema inicializado automáticamente
- **Mock Trader** conectado a la DB con restart automático

### 5. Verificar

```bash
# Ver que los contenedores están corriendo
docker compose ps

# Ver logs en tiempo real
docker compose logs -f trader

# Ver solo los últimos 50 logs
docker compose logs --tail 50 trader
```

## Registrar un trader

```bash
# Registro desde dentro del contenedor
docker compose exec trader python scripts/register_trader.py \
    --name random_baseline --type Random \
    --buy-prob 0.05 --tp 0.04 --sl -0.04 --max-hold 72

# Registrar trader XGBoost (los modelos deben estar en data/models/)
docker compose exec trader python scripts/register_trader.py \
    --name xgboost_v1 --type XGBoost \
    --model-path data/models/xgboost_v1 \
    --tp 0.04 --sl -0.04 --max-hold 72 --min-confidence 0.80
```

## Ver estado

```bash
docker compose exec trader python scripts/status.py
```

## Operaciones comunes

```bash
# Parar todo
docker compose down

# Parar sin borrar datos (PostgreSQL persiste en volumen)
docker compose stop

# Reiniciar solo el trader (por ejemplo tras actualizar código)
docker compose up -d --build trader

# Actualizar código y reiniciar
cd .. && git pull && cd deploy
docker compose up -d --build trader

# Acceder a PostgreSQL directamente
docker compose exec postgres psql -U postgres -d mock_trader

# Borrar TODO (incluidos datos de la DB)
docker compose down -v
```

## Estructura de deploy/

```
deploy/
├── Dockerfile           # Imagen del trader (Python 3.12)
├── docker-compose.yaml  # Orquestación completa (DB + App)
├── .env.example         # Template de configuración
└── README.md            # Esta guía
```

## Notas

- **PostgreSQL** se expone en el puerto `15432` del host para acceso externo/debug.
- **Los datos de la DB** persisten en el volumen Docker `pgdata`. Un `docker compose down` NO los borra; usa `docker compose down -v` si quieres borrar todo.
- **Los logs** del trader se guardan en el volumen `trader_logs`.
- **Los modelos** se montan como read-only desde `data/models/` del repositorio.
- **Restart automático**: ambos servicios usan `restart: unless-stopped`, se levantan solos tras un reboot.
