import asyncpg
import asyncio

DB_CONFIG = {
    "user": "myuser",
    "password": "1308923033Sa",
    "database": "mydb",
    "host": "194.143.146.8",
    "port": 5432
}

DB_CONFIG_MUSIC = {
    "user": "myuser",
    "password": "1308923033Sa",
    "database": "musicUsersDb",
    "host": "194.143.146.8",
    "port": 5432
}

pool = None
pool_music = None

async def init_pools():
    global pool, pool_music
    pool = await asyncpg.create_pool(**DB_CONFIG)
    pool_music = await asyncpg.create_pool(**DB_CONFIG_MUSIC)
    await init_db()

async def init_db():
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                user_name TEXT,
                user_first_name TEXT
            );
            
            CREATE TABLE IF NOT EXISTS films (
                code INTEGER PRIMARY KEY,
                title TEXT,
                description TEXT,
                image_url TEXT
            );
            
            CREATE TABLE IF NOT EXISTS likedFilms (
                userId BIGINT,
                code INTEGER,
                PRIMARY KEY (userId, code),
                FOREIGN KEY (userId) REFERENCES users(user_id),
                FOREIGN KEY (code) REFERENCES films(code)
            );
            
            CREATE TABLE IF NOT EXISTS sponsores (
                id INTEGER PRIMARY KEY,
                channelName TEXT,
                channelUrl_pub TEXT,
                channelUrl_private TEXT,
                allowSkip BOOLEAN
            );
        """)

# === Методы работы с основной базой ===

async def add_user(user_id: int, user_name: str, first_name: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, user_name, user_first_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO NOTHING
        """, user_id, user_name, first_name)

async def get_user_count() -> int:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT COUNT(*) FROM users")
        return row['count']

async def show_movie(code: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT title, description, image_url FROM films WHERE code = $1", code)
        return row

async def add_movie(code: int, title: str, description: str, image_url: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO films (code, title, description, image_url)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (code) DO NOTHING
        """, code, title, description, image_url)

async def delete_movie(code: int):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM films WHERE code = $1", code)

async def get_liked_movies(user_id: int):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT code FROM likedFilms WHERE userId = $1", user_id)
        return [row['code'] for row in rows]

async def add_liked_movie(user_id: int, movie_code: int):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO likedFilms (userId, code)
            VALUES ($1, $2)
            ON CONFLICT (userId, code) DO NOTHING
        """, user_id, movie_code)

async def remove_liked_movie(user_id: int, movie_code: int):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM likedFilms WHERE userId = $1 AND code = $2", user_id, movie_code)

async def get_sponsors():
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, channelName, channelUrl_pub, channelUrl_private FROM sponsores WHERE allowSkip = false")
        return rows
    
async def music_user_exists(user_id: int) -> bool:
    async with pool_music.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT 1 FROM users WHERE id = $1",
            user_id
        )
        return row is not None