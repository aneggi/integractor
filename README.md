INTEGRACTOR
============

Integractor example

Components are:

producer        -> port: 5552,5553
transformer     -> port: 5554
consumer        -> port: 5555
*If you run also webserver for index.html -> suggested port: 5500


# HOW TO RUN IT

##Info

* This system is executed on Ubuntu 24 with docker 27 installed, python3 3.12

## EXECUTE

* Open the folder and execute the command: 
    docker-compose up --force-recreate

* Install dependencies or create an enviroment

* Activate enviroment if needed
    source /envname/bin/activate

* Install modules
    pip install -r requirements.txt 

* You have two way to execute the demo system: one-by-one or all.
    ALL --> python3 simulate.py  which run all different actors
    ONE-BY-ONE --> python3 simulate_A.py  which run all only the actor you want to try



## Verify 
    http://localhost:15672/#/
    With USER and PASSWORD: demo

    There is a simple cockpit on the file (is a static file with JS):
    "Index.html" and you can start and stop specific component with the buttons




# HOW TO CREATE VIRTUAL ENVIROMENT ----------


## WINDOWS
* Create virtual enviroment
py -m venv venv

* Activate
.\venv\Scripts\Activate

## UBUNTU
* INSTALL venv
    pip install virtualenv

* Create
python3 -m venv integractor

* Activate
source integractor/bin/activate

# PUBLICATIONS:

This part will be completed after the first offical research pubblicaiton...

Note that this is part of the replication package of: "From Big-Bang to Building Blocks: Rethinking Integration in Reactive Software Projects"