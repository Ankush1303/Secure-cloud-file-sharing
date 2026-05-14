================================================================================
SECURE CLOUD FILE SHARING SYSTEM - FIRST-TIME SETUP (WINDOWS CMD)
================================================================================

STEP 1: OPEN COMMAND PROMPT (CMD)
---------------------------------
Press Win + R, type "cmd", press Enter.

STEP 2: NAVIGATE TO PROJECT FOLDER
----------------------------------
cd cloud_secure_storage

STEP 3: CREATE VIRTUAL ENVIRONMENT
----------------------------------
python -m venv venv

STEP 4: ACTIVATE VIRTUAL ENVIRONMENT
------------------------------------
venv\Scripts\activate.bat

Your prompt should now show (venv) at the beginning.

STEP 5: INSTALL DEPENDENCIES
----------------------------
python -m pip install --upgrade pip
pip install -r requirements.txt

STEP 6: CREATE ENVIRONMENT FILE
-------------------------------
copy .env.example .env

STEP 7: GENERATE RSA MASTER KEY
-------------------------------
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Copy the output string (looks like: gAAAAABk1234567890...).
Open .env in Notepad:
    notepad .env

Paste the generated key into this line:
    RSA_MASTER_KEY=your-generated-key-here

Also fill in:
    SECRET_KEY=any-random-string-min-32-characters-long
    JWT_SECRET_KEY=different-random-string-here

Save and close Notepad.

STEP 8: DELETE OLD DATABASE (IF ANY)
------------------------------------
del cloudsecure.db

STEP 9: CREATE DATABASE TABLES
------------------------------
python -c "from app import create_app; app=create_app(); app.app_context().push(); from app.extensions import db; db.create_all(); print('Database tables created!')"

STEP 10: RUN THE APPLICATION
----------------------------
python run.py

STEP 11: OPEN IN BROWSER
------------------------
Open your browser and go to:
    http://localhost:5000

================================================================================
QUICK START TEST
================================================================================

1. Click "Get Started" to create an account (e.g., username: ankush)
2. Log in and upload a file
3. Log out
4. Create another account (e.g., username: naman)
5. Log in as ankush, click Share on the file, enter "naman"
6. Log out
7. Log in as naman
8. You will see "Shared With Me" section - click Download

================================================================================
TROUBLESHOOTING
================================================================================

Problem: "ModuleNotFoundError"
Fix: Make sure you ran "venv\Scripts\activate.bat" and "pip install -r requirements.txt"

Problem: "SECRET_KEY must not be empty"
Fix: Edit .env file and fill in SECRET_KEY and JWT_SECRET_KEY

Problem: "Download failed: Decryption failed"
Fix: Make sure you are using the file_service.py with the share fix (re-encrypted keys)

Problem: "S3 upload failed"
Fix: You are using cloud mode. Switch to local mode by using local.txt code in file_service.py

Problem: Port 5000 in use
Fix: Change port in run.py or close other apps using port 5000

================================================================================
SWITCHING BETWEEN LOCAL AND CLOUD STORAGE
================================================================================

LOCAL MODE (no AWS needed):
    Replace app/services/file_service.py with the code from local.txt

CLOUD MODE (AWS S3):
    Replace app/services/file_service.py with the code from cloud.txt
    Add AWS credentials to .env file:
        AWS_ACCESS_KEY_ID=your-key
        AWS_SECRET_ACCESS_KEY=your-secret
        AWS_S3_BUCKET=your-bucket
        AWS_S3_REGION=us-east-1

================================================================================
TEAM
================================================================================
Ankush Vashisht (2236699)
Aryan Negi (2236718)
Jnardhan Sahani(2236833)
Chandigarh Engineering College