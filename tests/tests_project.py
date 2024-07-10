"""
Тесты для проекта.

Для тестирования используется библиотека pytest.

Тесты проверяют корректность работы функций из модуля main.py и repo_utils.py.
"""
import asyncio
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import NonCallableMock, patch

import aiofiles
import aiohttp
import pytest
from aioresponses import aioresponses

# Импортируем функции из вашего модуля
from main import main
from repo_utils import compute_hashes_for_repos, compute_sha256, download_repo

# URL репозитория
REPO_URL = 'https://gitea.radium.group/radium/project-configuration'
HEAD_URL = '{REPO_URL}/archive/master.zip'.format(REPO_URL=REPO_URL)

REPO_COUNT = 3

HTTP_SUCCESS = 200


@pytest.mark.asyncio()
async def test_download_repo():  # noqa:WPS210,SC100
    with aioresponses() as aioresponse:
        # Подделка ответа
        aioresponse.get(HEAD_URL, status=HTTP_SUCCESS, body=b'zipfilecontent')

        async with aiohttp.ClientSession() as session:
            with tempfile.TemporaryDirectory() as temp_dir:
                dest = Path(temp_dir) / 'repo.zip'
                await download_repo(session, HEAD_URL, dest)

                # Проверяем, что файл был создан
                # и его содержимое соответствует подделке
                async with aiofiles.open(dest, 'rb') as temp_file:
                    content_file = await temp_file.read()
                    assert content_file == b'zipfilecontent'


@pytest.mark.asyncio()
async def test_compute_sha256():  # noqa:WPS210,SC100
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / 'testfile'
        test_content = b'test content for hashing'

        # Создаем тестовый файл
        async with aiofiles.open(file_path, 'wb') as test_file:
            await test_file.write(test_content)

        # Вычисляем SHA256
        result_hash = await compute_sha256(file_path)

        # Ожидаемый хэш
        expected_hash = hashlib.sha256(test_content).hexdigest()

        assert result_hash == expected_hash


@pytest.mark.asyncio()
async def test_compute_hashes_for_repos():  # noqa:WPS210,SC100
    with (
        patch('repo_utils.download_repo'),
        patch('repo_utils.compute_sha256'),
    ) as (mock_download_repo, mock_compute_sha256):
        # Настраиваем поддельные результаты для мока
        mock_download_repo.return_value = asyncio.Future()
        mock_download_repo.return_value.set_result(None)

        fake_hashes = [
            'fakehash_{num}'.format(num=num)
            for num in range(REPO_COUNT)
        ]
        futures = [asyncio.Future() for _ in range(REPO_COUNT)]
        for future, fake_hash in zip(futures, fake_hashes):
            future.set_result(fake_hash)

        mock_compute_sha256.side_effect = futures

        with tempfile.TemporaryDirectory() as temp_dir:
            await compute_hashes_for_repos(
                temp_dir, REPO_COUNT, HEAD_URL,
            )

            # Проверяем, что функции скачивания и вычисления хэша были вызваны
            assert mock_download_repo.call_count == REPO_COUNT
            assert mock_compute_sha256.call_count == REPO_COUNT

            # Проверяем возвращенные хэши
            future_results = [future_f.result() for future_f in futures]
            assert future_results == fake_hashes


@pytest.mark.asyncio()
@patch('main.compute_hashes_for_repos')
async def test_main(mock_compute_hashes: NonCallableMock):
    await main()

    # Проверяем, что функция была вызвана
    mock_compute_hashes.assert_called_once()
    assert mock_compute_hashes.call_args[1]['repo_count'] == REPO_COUNT
    assert mock_compute_hashes.call_args[1]['head_url'] == HEAD_URL
