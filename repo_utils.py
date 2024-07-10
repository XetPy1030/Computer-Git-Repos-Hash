"""Модуль для работы с репозиториями."""

import asyncio
import hashlib
import logging
from pathlib import Path

import aiofiles
import aiohttp

logger = logging.getLogger(__name__)

CHUNK_SIZE = 8192

REPO_ZIP_FORMAT = 'repo_{num}.zip'


async def download_repo(
    session: aiohttp.ClientSession, url: str, destination: Path,
) -> None:
    """
    Функция download_repo.

    Скачивает репозиторий по-указанному URL
    и сохраняет его в указанное место.
    """
    async with session.get(url) as response:
        response.raise_for_status()
        async with aiofiles.open(destination, mode='wb') as repo_file:
            await repo_file.write(await response.read())
        logger.info(
            'Downloaded {url} to {destination}',
            extra={
                'url': url, 'destination': destination,
            },
        )


async def compute_sha256(file_path: Path) -> str:
    """Вычисляет SHA256 хэш файла."""
    sha256_hash = hashlib.sha256()
    async with aiofiles.open(file_path, mode='rb') as hash_file:
        while True:
            chunk = await hash_file.read(CHUNK_SIZE)
            if not chunk:
                break

            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


async def compute_hashes_for_repos(
    repos_dir: str, repo_count: int, head_url: str,
) -> list[str]:
    """
    Функция для вычисления хешей репозиториев.

    Скачивает несколько репозиториев, вычисляет для каждого SHA256 хэш
    и выводит его на экран.
    """
    repos_dir_path = Path(repos_dir)

    async with aiohttp.ClientSession() as session:
        # Скачиваем репозитории
        await download_repos(head_url, repo_count, repos_dir_path, session)

        hashes = await compute_few_sha256(repo_count, repos_dir_path)

        for num, hash_value in enumerate(hashes):
            logger.info(
                'SHA256 for repo_{num}.zip: {hash_value}',
                extra={
                    'num': num,
                    'hash_value': hash_value,
                },
            )

    return hashes


async def compute_few_sha256(
    repo_count: int, repos_dir_path: Path,
) -> list[str]:
    """Считает sha256 хэши для каждого скачанного файла."""
    hash_tasks = [
        compute_sha256(
            repos_dir_path / REPO_ZIP_FORMAT.format(num=repo_num),
        )
        for repo_num in range(repo_count)
    ]
    return await asyncio.gather(*hash_tasks)


async def download_repos(
    head_url: str,
    repo_count: int,
    repos_dir_path: Path,
    session: aiohttp.ClientSession,
) -> None:
    """Скачивает несколько репозиториев."""
    tasks = [
        download_repo(
            session,
            head_url,
            repos_dir_path / REPO_ZIP_FORMAT.format(num=repo_num),
        )
        for repo_num in range(repo_count)
    ]
    await asyncio.gather(*tasks)
