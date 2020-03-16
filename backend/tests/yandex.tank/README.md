###### Документация

https://yandex.ru/dev/tank/
https://yandextank.readthedocs.io/en/latest/
https://gist.github.com/sameoldmadness/9abeef4c2125bc760ba2f09ee1150330
https://www.youtube.com/watch?v=gws7L3EaeC0
https://overload.yandex.net/

###### Запуск контейнера с Yandex.Tank

docker run -v $(pwd):/var/loadtest --net host -it direvius/yandex-tank

###### Если нужно что-нибудь сделать перед запуском Танка

docker run -v $(pwd):/var/loadtest --net host -it --entrypoint /bin/bash direvius/yandex-tank