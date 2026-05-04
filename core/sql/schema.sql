CREATE TABLE IF NOT EXISTS calories_config (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT UNIQUE NOT NULL,
    daily_calories INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS products (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_name        TEXT UNIQUE NOT NULL,
    calories_per_hundred INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS user_calories_history (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT NOT NULL,
    calories    NUMERIC(8, 2) NOT NULL,
    product_name TEXT NOT NULL,
    order_id    INTEGER NOT NULL,
    date        DATE NOT NULL DEFAULT CURRENT_DATE
);