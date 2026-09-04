# Wall
## a real world open source example of FastAPI
### some features:
- Compliance with the principles of test writing FastAPI
- Compliance with the principles of clean coding
- Dockerized
- Using the nginx web server
- Documented and visualized by Swagger
#### Wall is a FastAPI project to share advertisements
#### If you want to get a good understanding of API and FastAPI, fork the project and participate in its development.
- In terminal: `git clone https://github.com/amirhamiri/wall`
- cd `/wall` Where the wall package is
- In terminal: `python -m venv venv`
- activate your venv: in windows `cd venv\scripts\activate` in linux: `venv/bin/activate`
- Run `pip install requirements.txt`
- Run `uvicorn wall.main:app`
- Visit http://127.0.0.1:8000/swagger to watch the api documentation
## Run project with docker
make sure you`ve installed docker
- In terminal: `git clone https://github.com/amirhamiri/wall`
- cd `/wall` Where the docker-compose.yaml is
- In terminal: `docker-compose up -d`
- Visit http://127.0.0.1:8000/swagger to watch the api documentation
that`s it...
