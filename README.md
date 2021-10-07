Installing
==========

To run Palanaeum on your local machine for development purposes, the easiest way is to use our provided Docker Compose setup.
Simply run `docker-compose up` to launch all required services.

When you run the app for the first time, you'll also want to create a superuser. To this end, run the following command:
```shell
docker-compose exec web python3 manage.py createsuperuser
```

Palanaeum should be reachable at http://127.0.0.1:9000/ after a successful launch.

Any changes you make to Palanaeum project files are automatically included in the container, so you can see
the results of your work instantaneously! :)

Note: Audio playback isn't working 100% correctly on the Django dev server. It doesn't support skipping to selected
part of the audio file, so you'll have to believe me that this functionality will work on a proper Nginx server ;)

Updating the sources
====================
From time to time you'll need to pull new changes made by others. This may include
changes in requirements and in database structure. To keep all dependencies updated, here's
what you should do after pulling the newest sources from repository.

```
# This ensures you have the latest dependencies installed
docker-compose up --build
# This performs any required database migrations
docker-compose exec web python3 manage.py migrate
```

This way, all necessary libraries should be installed and database structure should be
updated.

Setting up Sites module
=======================
Edit Site objects in database, to set proper domain name and site name.

Generating API keys
===================
If you want to allow unlimited access to API for someone, you need to
create an authentication token for them:

```
./manage.py drf_create_token <username>
```

This token should be added to HTTP requests inside a header:

```
Authorization: Token put_your_token_here
```
