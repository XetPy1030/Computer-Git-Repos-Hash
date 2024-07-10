"""Главный файл для запуcка проекта."""

import asyncio
import tempfile

from repo_utils import compute_hashes_for_repos

# URL репозитория
REPO_URL = 'https://gitea.radium.group/radium/project-configuration'
HEAD_URL = '{REPO_URL}/archive/master.zip'.format(REPO_URL=REPO_URL)

REPO_COUNT = 3


async def main() -> None:
    """Основная функция."""
    with tempfile.TemporaryDirectory() as temp_dir:
        await compute_hashes_for_repos(
            repos_dir=temp_dir,
            repo_count=REPO_COUNT,
            head_url=HEAD_URL,
        )


if __name__ == '__main__':
    asyncio.run(main())
