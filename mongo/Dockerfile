FROM mongo:7

# Seed data is copied at build time. The init script runs only when the data volume is empty,
# so later writes made by the app are never overwritten by a container restart.
COPY data/orders.json /seed/orders.json
# Host copies may be mode 600; the mongodb user inside the image must be able to read them.
RUN chmod 644 /seed/orders.json
COPY init-seed.sh /docker-entrypoint-initdb.d/10-seed.sh

ENV MONGO_INITDB_DATABASE=systemone
EXPOSE 27017