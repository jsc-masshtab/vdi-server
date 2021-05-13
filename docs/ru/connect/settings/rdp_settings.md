# Настройки RDP

Для оптимальной работы подключения **RDP** необходимо воспроизвести следующие шаги:

1. Убедитесь, что вашим доменным пользователям разрешено подключение с использованием службы [удаленных рабочих столов](../../broker/how_to/rdp/example_rdp_domain.md)
   
1. Запустив тонкий клиент, перейдите в раздел **Настройки -> RDP** и убедитесь в активности опции h264 (если работа планируется с использованием NATIVE_RDP опция не важна).

!!! example "RDP"
    ![image](../../../_assets/vdi/thin_client/connect_settings_rdp.png)

1. Перейдите в раздел **Настройки -> Основные** и активируйте переключатель **Внешняя служба авторизации**.

1. Выполните подключение к пулу и убедитесь в корректности настроек

!!! info "При подключении к брокеру с использованием контроллера **MS AD** имя пользователя может быть следующего вида:"
   - Без указания домена, например, *user1* - в таком случае, домен будет подставлен из поля **Имя домена** указанном 
        в настройках **Службы каталогов** на брокере.
   - С указанием домена, например, *user1@domain*, *domain\user1*, *domain/user1* - в таком случае, имя пользователя будет
        передано напрямую, без предварительной обработки. Данный способ не рекомендуется к использованию.

1. Формат изображения. Рекомендуется BGRA32.

1. Параметр FPS задает частоту обновления экрана.

1. Поле **Перенаправляемые папки** предназначено для задания списка папок, которые будут перенаправлены в ВМ. 
Перечислите папки через точку с запятой, либо выберите их с помощью селектора **Добавить папку**.

1. При включенной опции **Мультимониторность** приложение использует до 3 доступных мониторов. Рекомендуется, чтобы 
на всех мониторах было задано одинаковое разрешение. 

1. При включенной опции **Перенаправлять принтеры** сетевые принтеры будут перенаправлены в ВМ.

1. При включенной опции **Запустить приложение** будет запущено выбранное приложение.
[Запуск в режиме доступа одного приложения](../one_app_mode.md)

!!! note ""
    В разделе **Настройки -> Основные** есть поле *Домен*. Данное поле используется **ТОЛЬКО** для подключения к RDP и
    не задействуется в авторизации на брокере. Рекомендуется использовать только как диагностическую меру.
      
      