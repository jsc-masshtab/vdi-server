## Инструкция для тонкого клиента


База данных называется vdi (пока), ей владеет юзер postgres.

```
postgres=# create datavase vdi;
```
Применяем миграции

```
mi apply
```

Переходим на `/admin`, видим веб-консоль graphiql
```

```

<table><tr><td>
<pre>
mutation {
 createTemplate(image_name: "disco") {
  id
 }
}
</pre>
</td><td>
<pre>
{
  "data": {
    "createTemplate": {
      "id": "4e2f5ca4-242f-4318-add7-cd936d88548f"
    }
  },
  "errors": null
}
</pre>
</tr></table>

Этот запрос поищет среди загруженных файлов `*disco*.qcow2`. В случае успеха создаст виртуалку и вернёт id.
В случае, если template vm уже создана, можно выполнить

```
mutation {
 addTemplate(id: "6ad6fb58-ba94-46d8-9769-f445c68dc44e") {
  ok
 }
}
```

Добавляем пул:

<table><tr><td>
<pre>
mutation {
 addPool(name: "pub-1", template_id: "6ad6fb58-ba94-46d8-9769-f445c68dc44e"){
  id
 }
}
</pre>
</td><td>
<pre>
{
  "data": {
    "addPool": {
      "id": 2
    }
  },
  "errors": null
}
</pre>
</tr></table>

API для тонкого клиента будет брать пул, содержащий "pub" в названии (потому что пока нет юзеров)


Через некоторое время в пуле появятся свободные виртуалки:

<table><tr><td>
<pre>
{
 pool(id: 2) {
  state {
    available {
      id
    }
  }
 }
}
</pre>
</td><td>
<pre>
{
  "data": {
     "pool": {
       "state": {
         "available": [
           {
            "id": "c16e6cb2-4cc6-44f9-8e5b-8432fcd1b490"
           },
           {
            "id": "86cf35bc-5a22-48dc-8ade-82d27e48826e"
           }
         ]
     }
     }
  },
  "errors": null
}
</pre>
</tr></table>


Теперь, собственно, API для клиента:

```
POST /client

{"e4242e6a-c6a6-4f70-82ce-1520c5a0e7c2": <что-нибудь>
```
