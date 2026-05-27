# cashback_payment_bot

## Environment

Use `.env` with values from `.env.dist`.

Required variables:
- `BOT_TOKEN`
- `SUPERBANKING_API_KEY`
- `SUPERBANKING_CABINET_ID`
- `SUPERBANKING_PROJECT_ID`
- `SUPERBANKING_CLEARING_CENTER_ID`
- `REDIS_URL`

For Docker Compose deployments Redis is started as the `redis` service, and the
bot container uses `redis://redis:6379/0`.

## Payout safety

- Before each payout, bot requests `post_api_balance`.
- If `balance < BALANCE_LIMIT_EXECUTION` from `src/core/constants.py`, payout is blocked.

## Persistent `pay_number`

`orderNumber` is generated from Redis atomic counter (`INCR`) with key:

`cashback_payment:pay_number:<cabinet_id>:<project_id>:<clearing_center_id>`

This prevents counter reset after process restart and keeps sequence unique per account.
Docker Compose stores Redis data in the `redis_data` volume.

## CI/CD

GitHub Actions:
- `CI` (`.github/workflows/ci.yml`): installs dependencies and runs compile smoke-check.
- `CD` (`.github/workflows/cd.yml`): builds Docker image, pushes to GHCR, optional SSH deploy.

For `CD` deploy job set repository secrets:
- `DEPLOY_HOST`
- `DEPLOY_USERNAME`
- `DEPLOY_SSH_KEY`
- `DEPLOY_PATH`
- optional `DEPLOY_PORT` (default `22`)
