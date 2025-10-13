
rm -Force -Recurse -Confirm:$false node_modules
rm -Force -Recurse -Confirm:$false .next

cp -Force .env.dev .env.local
npm install --legacy-peer-deps
# pnpm run generate:api:force
npm build
