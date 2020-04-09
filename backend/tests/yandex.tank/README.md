###### Документация

https://yandex.ru/dev/tank/
https://yandextank.readthedocs.io/en/latest/
https://gist.github.com/sameoldmadness/9abeef4c2125bc760ba2f09ee1150330
https://www.youtube.com/watch?v=gws7L3EaeC0
https://overload.yandex.net/
https://yandextank.readthedocs.io/en/latest/ammo_generators.html

###### Как пользоваться?
1. Положить api-token от сервиса для онлайн-просмотра результатов в файл token.txt
`echo 'fa30617b49bb4dadb2820fa3511ce420' >> $PYTHONPATH/tests/yandex.tank/token.txt`
2. Актуализировать load.yaml для кейса.
2. Выполнить генерацию патронов для кейса.
3. Запустить контейнер с Yandex.Tank для кейса.
4. Посмотреть результаты на https://overload.yandex.net/ 

###### Генерация патронов

1. Запустить тестируемый vdi-server
2. Запустить генератор патронов
`cd $PYTHONPATH/tests/yandex.tank && python make_ammo.py --mode create --users_count 100 --remote_host '192.168.6.52'`

###### Запуск контейнера с Yandex.Tank

docker run -v $(pwd):/var/loadtest --net host -it direvius/yandex-tank

###### Если нужно что-нибудь сделать перед запуском Танка

docker run -v $(pwd):/var/loadtest --net host -it --entrypoint /bin/bash direvius/yandex-tank