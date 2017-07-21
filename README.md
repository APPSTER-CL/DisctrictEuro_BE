
# District Euro Backend

This repo holds district euro web api.

## Software required

     python 2.7.x
     postgresql 9.5 or later


## Clone repository

     git clone git@github.com:APPSTER-CL/DisctrictEuro_BE.git

## Create the environment

     pip install virtualenv
     cd disctricteuro_be
     virtualenv venv

## Activate virtual environment

On windows

     source venv/Scripts/activate

On MAC

     source venv/....../activate

## Install dependencies

     pip install -r district_euro/requirements.txt


## Create database

Connect to your postgres server and create a new database.

Configure database name and connection parameters in the project. Edit the file district_euro/district_euro/settings.py and set the DATABASES variable to:

     DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'database_name', # The name you set when creating the database
            'USER': 'database_user',
            'PASSWORD': 'database_password',
            'HOST': 'database_host', # localhost most likely
        }
    }

## Let django create tables

CD to district_euro root directory and run:


     python manage.py migrate


## (Optional) Load some initial data

     python manage.py loaddata initial_data.yaml

## Run development server

     python manage.py runserver 0.0.0.0:8000


## Getting the last version

When pulling the last version from the repository you might have conflicts with your modified local version. If you dont want to commit those changes you can undo all of them by runnig:

      git checkout -- .

This will erase your database configuration in settings.py.

Then pull code like always:

     git pull origin master

# Usage

Once the server is running you can access api documentation on: http://localhost:8000/docs

In district_euro/core/tests/ are all the automatic tests that need to be ran before committing changes.

Services under account are for authentication token retrieve/update.

Services under api are for district_euro logic. The services that prefix the type of user in the path require authentication, the rest doesnt.

You can try services directly on /docs page. To test a service that require authentication you can place the token in the upper swagger navbar where it says api_key, then just click the 'Try it out' button to execute it.

## Authentication/Authorization

To obtain an access token call the /account/login with the credentials.
To use that access token include the Authorization header like this:

     Authorization: Token <access_token>
