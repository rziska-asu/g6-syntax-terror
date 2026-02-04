Music Discovery Engine


Tech Used:

Python

Streamlit (frontend UI)

MySQL Server + MySQL Workbench (database)

Last.fm API (via pylast)

iTunes Search API (track previews)

bcrypt (password hashing)


 Install First:

Make sure the following are installed before setup:

Python 3.11+

MySQL Server

MySQL Workbench

Git

* MySQL must be running locally.

 Developer Setup
1. Activate the virtual environment

From the project root:

Windows (PowerShell):

.\venv\Scripts\Activate.ps1


You should see (venv) in the terminal.

2️. Install Python dependencies
pip install -r requirements.txt

This installs all required libraries for the project.

3️. Create your .env file

Create a file named .env in the project root (template provided in .env.example. You can rename it to .env).

*Host, port, and database name should usually stay the same

The Last.fm key is in discord

 Database Setup

Open MySQL Workbench

Connect to your local MySQL server

Click file, open SQL script and select MUSIC.SCHEMA.sql


The following tables should appear:

users

user_sessions

liked_tracks

history_runs

 !! Verification Tests !!
 Test that you setup .env correctly

Run:

python env_test.py in VS code terminal

 Test database connection

Run:

python db_smoketest.py in VS code terminal

Expected results:

Connected to database: music_discovery_engine
Tables found:
 - users
 - user_sessions
 - liked_tracks
 - history_runs
DB smoke test PASSED.


If this passes, your setup is correct.

Helpful Notes for Team Members

Do not commit .env or venv/

Everyone runs their own local MySQL server

If db_smoketest.py fails, fix setup before touching app code

If it passes, you’re good to start developing!