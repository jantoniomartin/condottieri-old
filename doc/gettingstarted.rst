Getting started
===============

The following are some basic guidelines to setup a **Condottieri** server,
like the one in http://condottierigame.net.

Maybe you want to host your own game server, or maybe you want to add new
features to Condottieri and you have to test them before sending them to the
repository. In any case, you will need to setup a new server.

Prerequisites
+++++++++++++

Before installing **Condottieri**, there are some important pieces that you
have to install in your machine. Some of them are optional.

Operating system
----------------

So far, **Condottieri** has lived only in Linux machines. However, since all
the required software is multiplatform, you can try to use a different, but
less cute, operating system. Please, if it works, tell us.

Python and virtual-env
----------------------

The very first part you will need is Python. Instead of using the Python
interpreter and libraries that maybe are already in your system, it's
advisable, safer and cleaner to use virtual-env. Install virtual-env, which
includes Python, **activate** the environment, and then install the rest of
elements in this virtual environment.

.. warning::
   The code in ``condottieri`` has been tested only in versions 2.5 and 2.6
   of Python. Maybe they work in different versions, but I don't know.

Django
------

Once you have a *pythonic* environment, you have to install django. As before,
maybe you already have django in you machine. Don't use it. Install a new
instance in your virtual environment.

::

    $ pip install django --upgrade

Pinax
-----

Install Pinax (version 0.9 or higher).

.. warning::
   In this moment, 0.9 is the development version of Pinax. **Condottieri** has
   been tested only in this version.

Other libraries
---------------

If not installed by Pinax, you will need some other libraries in your virtual
environment. Just install them using *pip*:

::
    
    $ pip install mysql-python
    $ pip install django-pagination

Optional, recommended libraries
-------------------------------

Just like above, you may need to install the following packages. It is highly
recommended that you install *south*. Regarding *django-notification*, you
will need the version 0.2.0 or higher.

::
    
    $ pip install south
    $ pip install jogging
    $ pip install django-notification


Installing Condottieri
++++++++++++++++++++++

Hopefully, at this point you will have your environment to run **Condottieri**.
First of all, make a local, work copy of the repository, either with *git* or
downloading a tarball.

You have to follow the next steps inside your local copy.

Configuration files
-------------------

Your local copy includes the file ``settings.py``, with default configurations
taken from Pinax. This file imports another file, ``local_settings.py``, that
you have to create and edit to suit your needs. The file
``local_settings.py.example`` includes some constants that you may want to
edit and use.

Don't forget to configure (and create, if you don't use sqlite) a database.

Sync the database
-----------------

Once you have customized your settings, you have to populate your database
with tables and initial data.

::
    
    $ python manage.py syncdb

