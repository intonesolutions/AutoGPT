read autogpt_platform/_eks/_publish.ps1

after pulling and merging from main fork:
1- in backend, remove .venv and run: poetry install
1.5- then run : poetry lock
2- generate prisma client: poetry run prisma generate
3- update the db: poetry run prisma migrate dev (reset if you have to)
            or run all the migration sql scripts if you know where to start from

2- in frontend