# follow https://elatov.github.io/2018/06/install-guacamole-on-docker/

source .env
docker run --rm guacamole/guacamole /opt/guacamole/bin/initdb.sh --mysql > initdb.sql
docker exec -i guacamole-mysql-db bash -c 'mysqladmin -u root -p"$MYSQL_ROOT_PASSWORD" create guacamole'
sleep 1
docker exec -i guacamole-mysql-db bash -c 'exec mysql -u root -p"$MYSQL_ROOT_PASSWORD" guacamole -e "CREATE DATABASE guacamole;"'
sleep 1
docker exec -i guacamole-mysql-db bash -c 'exec mysql -u root -p"$MYSQL_ROOT_PASSWORD" guacamole -e "CREATE USER \""$MYSQL_USER"\" IDENTIFIED BY \""$QUAC_PASSWORD"\";"'
sleep 1
docker exec -i guacamole-mysql-db bash -c 'exec mysql -u root -p"$MYSQL_ROOT_PASSWORD" guacamole -e "GRANT SELECT,INSERT,UPDATE,DELETE,CREATE ON guacamole.* TO \"guac\"@\"%\";"'
sleep 1
docker exec -i guacamole-mysql-db bash -c 'exec mysql -u root -p"$MYSQL_ROOT_PASSWORD" guacamole -e "FLUSH PRIVILEGES;"'
sleep 1
docker exec -i guacamole-mysql-db bash -c 'exec mysql -u root -p"$MYSQL_ROOT_PASSWORD" guacamole ' < initdb.sql

# Access to guacamole with http://{docker-ip}:8084/guacamole/