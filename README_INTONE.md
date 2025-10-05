ensure py (python launcher) is installed:
winget install --id Python.Launcher -e

read autogpt_platform/_eks/_publish.ps1

after pulling and merging from main fork:
A. backend
    1- in backend, remove .venv 
    2- run: poetry env use C:\Users\tshaz\AppData\Local\Programs\Python\Python311\python.exe
    3- run: poetry install
    4- then run : poetry lock
    5- make sure you are connected to the vpn with AWS and the db is accessible
    6- generate prisma client: poetry run prisma generate
    7- update the db: poetry run prisma migrate dev (reset if you have to)
                or run all the migration sql scripts if you know where to start from
    8- to run (debug), use the debugger (backend)
if need to upgrade python OR start over:
    1- winget install --id Python.Python.3.11 -e
    2- py -3.11 -V
    3- py -0p -- to find the installed versions and paths
    3- delete venv folder
    4- run: poetry env use C:\Users\tshaz\AppData\Local\Programs\Python\Python311\python.exe
    6- repeate steps in A. backend
B- in frontend
    1- npm install --legacy-peer-deps
    2- to run: npm run dev
    3- login: ts1@intone.ca and 123456

