BEGIN;

ALTER TABLE public.orders
    ADD COLUMN IF NOT EXISTS idempotency_key UUID,
    ADD COLUMN IF NOT EXISTS request_hash TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS
    uq_orders_user_idempotency_key
ON public.orders (user_id, idempotency_key)
WHERE idempotency_key IS NOT NULL;

COMMIT;