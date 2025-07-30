### Hexlet tests and linter status:
[![Actions Status](https://github.com/solmael/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/solmael/python-project-83/actions)

[![SonarQube Cloud](https://sonarcloud.io/images/project_badges/sonarcloud-light.svg)](https://sonarcloud.io/summary/new_code?id=solmael_python-project-83)

# About Project

An educational project on the Hexlet platform. A Flask application that analyzes web pages for SEO readiness.

## Installation

You can use a ready-made project (the database is valid until 2025.08.27):
https://python-project-83-evxz.onrender.com/

Installation on PC:
```sh
git clone git@github.com:solmael/python-project-83.git
cd python-project-83
```
Create a .env file and specify your PostgreSQL settings in the following format:
```sh
DATABASE_URL="postgresql://<имя пользователя>:<пароль пользователя>@localhost:5432/<имя базы данных>"
SECRET_KEY=strong_secret_key
```
Install uv and dependencies, verify the environment, create database tables:
```sh
make build
```
Start the application:
```sh
make start
```
Navigate to the link shown in the terminal.