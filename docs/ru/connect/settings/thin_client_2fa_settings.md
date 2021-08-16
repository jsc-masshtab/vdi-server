# Настройка двухфакторной аутентификации

!!! note "Примечание"
    Доступно начиная с версии VeiL Connect 1.7.0 и версии VeiL VDI 3.1.1.   
    При включении двухфакторной аутентификации при каждой авторизации будет требоваться
    одноразовый пароль, генерируемый приложением-аутентификатором (пример Яндекс.Ключ, Google Authenticator).

### Включение

1. Авторизируйтесь в VeiL Connect, введя имя пользователя/пароль и нажав **Войти**.

1. После успешной авторизации нажмите кнопку **Настройки профиля**.

    !!!
    ![image](../../_assets/vdi/thin_client/2fa/vdi_pools_window.png)

1. В открывшемся окне активируйте пункт **Двухфакторная аутентификация**.

    !!!
    ![image](../../_assets/vdi/thin_client/2fa/2fa_1.png)

1. Нажмите кнопку **Сгенерировать новый код**.

    !!!
    ![image](../../_assets/vdi/thin_client/2fa/2fa_2.png)

1. Отсканируйте QR-код c помощью аутентификатора (пример Яндекс.Ключ, Google Authenticator).

    !!!
    ![image](../../_assets/vdi/thin_client/2fa/2fa_3.png)

1. Нажмите **Применить**.

    !!!
    ![image](../../_assets/vdi/thin_client/2fa/2fa_4.png)
    
    
### Отключение

1. Зайдите в **Настройки профиля** и деактивируйте пункт **Двухфакторная аутентификация**.

1. Нажмите **Применить**.