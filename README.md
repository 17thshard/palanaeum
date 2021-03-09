Installing
==========

To run Palanaeum on your local machine for development purposes you need to set up a virtual machine.
That's super easy to do on Linux

1. Download and install:
    * VirtualBox: https://www.virtualbox.org/wiki/Downloads
    * Vagrant: https://www.vagrantup.com/downloads.html
    * If you're on Windows you need to have an ssh client installed, I suggest
      this solutions:
        1. Install git from: https://git-scm.com/download/win
        2. Add C:\Program Files\Git\usr\bin to your PATH system variable
           (this can be done by selecting "Use Git and optional Unix tools
            from the Windows Command Prompt" during Git installation).
        3. Check if typing `ssh` in your console works. If it does,
            reboot your machine to make sure everything works fine and proceed.

2. In your console, go to main palanaeum directory:

    ```
    cd <path to palanaeum>
    ```

3. Start up Vagrant virtual machine:

    ```
    vagrant up
    ```

    This step will take some time to complete. When you first start a vagrant box, it has to download a system image
    (couple hundreds MB) and install all required software in this system (another hundred MBs to donwload).
    Starting the system next time, will be faster though, as the state of the machine is not forgotten until you
    destroy it.

4. Once the machine is up and you're back in control of your console window, you can SSH into newly created virtual machine:

    ```
    vagrant ssh
    ```

5. Go to the directory where Palanaeum project is mapped:

    ```
    cd /vagrant
    ```

6. Create a superuser account (this should be done only once, when you first run the machine):

    ```
    python3 manage.py createsuperuser
    ```

7. And start up a django development server:

    ```
    python3 manage.py runserver_plus
    ```

8. Now you can get to work with Palanaeum! It's available from you host machine under this address:
    ```
    http://127.0.0.1:9000/
    ```

    Any changes you make to Palanaeum project files are automatically included in the virtual machine, so you can see
    the results of your work instantaneously! :)

Note: Audio playback isn't working 100% correctly on the Django dev server. It doesn't support skipping to selected
part of the audio file, so you'll have to believe me that this functionality will work on a proper Nginx server ;)

Now, when you're done with working with Palanaeum, remember to exit the virtual machine and call:

```
vagrant halt
```

to turn it off. Otherwise, it will continue to block resources on your computer until you reboot.
To start  working on Palanaeum again, just follow the instructions starting with step 2.

Running Celery
==============
To be able to process uploaded files, you need to have a Celery process running in the background
on the virtual machine. This can be achieved in many ways, one of which is to:

1. Start up a new terminal window
2. Log into the virtual machine using
    ```
    vagrant ssh
    ```
3. Starting the the Celery worker process:

    ```
    cd /vagrant
    celery worker -A palanaeum
    ```

4. Leave it working as long as you work with Palanaeum.


Updating the sources
====================
From time to time you'll need to pull new changes made by others. This may include
changes in requirements and in database structure. To keep all dependencies updated, here's
what you should do after pulling the newest sources from repository.

```
# This code should be executed inside the VM
cd /vagrant
sudo pip3 install -Ur requirements.txt
python3 manage.py migrate
```

This way, all necessary libraries should be installed and database structure should be
updated. If this fails, you can always fall back to:

```
# This should be executed on the host machine
vagrant destroy
vagrant up
```


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


Docker Notes

Create new DB:
docker run --name db_pala -e POSTGRES_PASSWORD=palanaeum --network host -d postgres

Start the DB after host reboot:
docker start db_pala

Create Redis instance
docker run --name redis_pala --network host -d redis

Start redis instance
docker start redis_pala

