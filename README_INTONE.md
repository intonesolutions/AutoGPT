read autogpt_platform/_eks/_publish.ps1

after pulling and merging from main fork:
1- in backend, remove .venv and run: poetry install
2- generate prisma client: poetry run prisma generate
3- update the db: poetry run prisma migrate dev (reset if you have to)

2- in frontend