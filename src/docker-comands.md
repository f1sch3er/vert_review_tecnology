
## COMANDOS DOCKER

# docker compose exec app python manage.py makemigrations
# docker compose exec app python manage.py migrate
# docker compose exec app python manage.py showmigrations

# RODAR O PROJETO
# docker compose up (AQUI O TERMINAL FICA PRESO, MAS VEMOS OS LOGS)
# docker compose up -d (AQUI O TERMINAL NÃO FICA PRESO)

# docker compose up --build (USAR QUANDO MUDAR ALGUMA CONFIGURAÇÃO REQUIREMENTS OU DOCKERFILE POIS INICIA SEM CACHE)

# docker compose down (REMOVER OS CONTAINERS)
# docker compose logs -f (VERIFICA LOG)

# docker compose restart web (REINICIA SERVIÇO ESPECIFICO)

