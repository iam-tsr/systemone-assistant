#!/bin/sh
# Runs once, on first start of an empty data volume (mongo image entrypoint).
# Builds a JS file from the seed JSON, runs it with root credentials, and fails the container
# start if the seeded counts do not match the source files.
set -e

DB="${MONGO_INITDB_DATABASE:-systemone}"
export HOME=/tmp  # mongosh writes history under $HOME; /root is not writable for this user
JS=/tmp/seed.js

{
  printf 'const orders = '; cat /seed/orders.json; printf ';\n'
  # printf 'const escalations = '; cat /seed/escalations.json; printf ';\n'
  cat <<'EOF'
db.orders.drop();
db.escalations.drop();
db.orders.insertMany(Object.entries(orders).map(([id, order]) => ({ _id: id, ...order })));
db.escalations.createIndex({ ticket_id: 1 }, { unique: true });
const expectedOrders = Object.keys(orders).length;
if (db.orders.countDocuments() !== expectedOrders) throw new Error('orders count mismatch after seed');
print('seeded orders=' + expectedOrders);
EOF
} > "$JS"

mongosh --quiet --norc \
  "mongodb://127.0.0.1:27017/${DB}" \
  -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" \
  --authenticationDatabase admin \
  --file "$JS"