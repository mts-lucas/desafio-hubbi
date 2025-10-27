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
│       └── tests.py           # Tests das views e das tasks
├── marketplace/               # Configurações Django
│   ├── settings.py
│   ├── celery.py
│   └── urls.py
├── docs/                      
│   ├── planilha.csv           # Planilha para ser usada nos testes
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
docker compose up --build -d
```

> O serviço `web` será exposto em [http://localhost:8000](http://localhost:8000) onde sera redirecionado para a interface do swagger onde podera testar os demais endpoints

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
curl -X POST http://localhost:8000/marketplace/api/v1/v1/token/ -d 'username=admin&password=senha'
```

Dentro da interface do Swagger, no inicio da pagina, deve se inserir o access token recebido para poder acessar os demais endpoints que são privados

##  Endpoints principais

* `GET marketplace/api/v1/parts/` — listar peças (autenticado)
* `GET marketplace/api/v1/parts/<id>/` — detalhes de uma peça (autenticado)
* `POST marketplace/api/v1/parts/` — criar peça (**apenas admin**)
* `PUT/PATCH marketplace/api/v1/parts/<id>/` — atualizar (**apenas admin**)
* `DELETE marketplace/api/v1/parts/<id>/` — excluir (**apenas admin**)
* `POST marketplace/api/v1/parts/import-csv/` — upload CSV (**apenas admin**, executado de forma assíncrona)

para testar o endpoint de importação de csv, utilize a planilha que está em `docs/planilha.csv`

##  Tarefas Celery

### 1. Importação CSV (assíncrona)

Executada ao enviar o arquivo via endpoint `marketplace/api/v1/parts/import-csv/`.
A task cria os registros no banco de dados em background.

### 2. Reposição automática de estoque

Executada diariamente via **Celery Beat**, conforme agendamento definido, onde todas as peças com quantidade < 10 são ajustadas para o mínimo de 10.

Para testar manualmente essa funcionalidade:

```bash
docker compose exec web bash
python manage.py shell
```

Dentro do Django Shell execute:

```bash
from apps.products.tasks import replenish_stock_minimum
replenish_stock_minimum.delay()
```

## Testes automatizados

Para rodar os testes:

```bash
docker compose exec web python manage.py test
```
