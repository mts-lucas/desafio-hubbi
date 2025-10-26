# Desafio Backend Hubbi

Este projeto é um **marketplace de autopeças** desenvolvido em **Django REST Framework**, com autenticação **JWT**, tarefas assíncronas via **Celery/Redis** e orquestração com **Docker Compose**, projetado como forma de avaliação no processo seletivo da Hubbi.

## Estrutura

```
desafio-hubbi/
├── apps/
│   └── products/
│       ├── models.py          # Modelo Part
│       ├── views.py           # CRUD + importação CSV
│       ├── tasks.py           # Tarefas Celery (importação e reposição)
│       └── tests/             
├── marketplace/               # Configurações Django
│   ├── settings.py
│   ├── celery.py
│   └── urls.py
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── requirements.txt
└── README.md
```

---

## Configuração do ambiente local

### 1. Copiar o arquivo `.env.example`

```bash
cp .env.example .env
```

### 2. Construir e subir os containers

```bash
docker compose up --build
```

> O serviço `web` será exposto em [http://localhost:8000](http://localhost:8000)

### 3. Acessar o container Django

```bash
docker compose exec web bash
```

### 4. Criar superusuário (admin)

```bash
python manage.py createsuperuser
```

### 5. (Opcional) Rodar migrações manualmente

```bash
python manage.py migrate
```



## Autenticação JWT

Endpoints:

```
POST marketplace/api/v1/v1/token/              # gera access e refresh tokens
POST marketplace/api/v1/token/refresh/         # renova token de acesso
```

Exemplo:

```bash
curl -X POST http://localhost:8000/api/token/ -d 'username=admin&password=senha'
```


##  Endpoints principais

* `GET marketplace/api/v1/parts/` — listar peças (autenticado)
* `GET marketplace/api/v1/parts/<id>/` — detalhes de uma peça
* `POST marketplace/api/v1/parts/` — criar peça (**apenas admin**)
* `PUT/PATCH marketplace/api/v1/parts/<id>/` — atualizar (**apenas admin**)
* `DELETE marketplace/api/v1/parts/<id>/` — excluir (**apenas admin**)
* `POST marketplace/api/v1/parts/import-csv/` — upload CSV (**apenas admin**, executado de forma assíncrona)


##  Tarefas Celery

### 1. Importação CSV (assíncrona)

Executada ao enviar o arquivo via endpoint `marketplace/api/v1/parts/import-csv/`.
A task cria os registros no banco de dados em background.

### 2. Reposição automática de estoque

Executada diariamente via **Celery Beat**, conforme agendamento definido, onde todas as peças com quantidade < 10 são ajustadas para o mínimo de 10.


## Testes automatizados

Para rodar os testes:

```bash
docker compose exec web pytest -v
```

Relatório de cobertura:

```bash
docker compose exec web pytest --cov=apps/products
```
