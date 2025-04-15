# back-django

# Setup DJANGO REST UI
1. Go to orders-service
2. Run ``python manage.py collectstatic --noinput``
3. If no local interpreter configured, go to docker and run in the container (container -> exec -> run command)

# Setup DB with dummy data
1. Go to container and run ``python manage.py init_db``
2. DB credentials for local can be found in orders-service/orders/settings/DATABASES