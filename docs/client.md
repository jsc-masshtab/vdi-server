
Получаем токен:

```
> curl -X POST http://127.0.0.1:8000/auth --data '{"username": "admin", "password": "<сами-знаете-что>"}'
{"access_token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwiZXhwIjoxNTU3MzE4NzU1LCJpYXQiOjE1NTczMTY5NTUsIm5iZiI6MTU1NzMxNzEzNX0.TVqFJhzxvPUNteIMSQe2qsh_7gdViSr1ARbKWIlc5AA"}
```

Запрашиваем список пулов

```
> curl -X GET -H "Authorization: jwt eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwiZXhwIjoxNTU3MzE4NzU1LCJpYXQiOjE1NTczMTY5NTUsIm5iZiI6MTU1NzMxNzEzNX0.TVqFJhzxvPUNteIMSQe2qsh_7gdViSr1ARbKWIlc5AA" http://localhost:8000/client/pools
[{"id":53,"name":"this"}]
```

Получаем виртуалку из пула

```
> curl -X POST -H "Authorization: jwt eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwiZXhwIjoxNTU3MzI5ODU1LCJpYXQiOjE1NTczMjgwNTUsIm5iZiI6MTU1NzMyODIzNX0.y2ponNrI-OtR0xh5AIipm9osLYG2ZJLt3IvOrD_nOEw" http://localhost:8000/client/pools/53
{"host":"192.168.20.120","port":5901}
```