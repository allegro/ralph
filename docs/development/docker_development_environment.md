# Ralph development environment

## Requirements

Make sure your host has the following requirements installed and
properly configured, if required:

1.  Docker 24.0.0 or later
1.  docker-compose

## Setting up Ralph in PyCharm IDE

From **Settings... -> Project: ralph -> Project Interpreters** choose **Add Interpreter -> On Docker**

Choose docker/Dockerfile-local-interpreter as Dockerfile and change context to "."

If you are using non amd64 architecture (ie. Apple Silicon), under Options -> Build options: add ```--platform linux/amd64```. Keep in mind, that this requires amd64 emulation in your docker environment.

![setup_dockerfile.png](img%2Fsetup_dockerfile.png)

After clicking Next, image should be successfully created and next step should provide you with proper path to interpreter:

![setup_docker_path.png](img%2Fsetup_docker_path.png)

Properly created environment should show all packages required by Ralph:

![setup_done.png](img%2Fsetup_done.png)

## Running local instance of Ralph from source code

To run local Ralph from source code using docker-compose issue this command:
```docker-compose -f docker/docker-compose-local-dev.yml up```

All required services should be started and your local ralph instance should be accessible on http://localhost:8000