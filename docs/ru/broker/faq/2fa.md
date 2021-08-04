# Двухфакторная аутентификация по одноразовому паролю

Двухфакторная аутентификация — это метод идентификации пользователя при помощи запроса аутентификационных данных двух 
разных типов: первый этап — это логин и пароль, второй — 6-значный одноразовый код. Одноразовые коды можно генерировать 
с помощью приложения — аутентификатора (2FA-приложения).

### Как работают приложения-аутентификаторы

Последовательность действий:

1. Необходимо установить на смартфон приложение (или воспользоваться веб-версией) для двухфакторной аутентификации 
   (Яндекс.Ключ, Google Authenticator, Authy, Microsoft Authenticator, 1password и пр.);
2. В настройках пользователя VeiL Broker необходимо [включить двухфакторную аутентификацию](../operator_guide/users.md)
   и сгенерировать QR код;
3. После сканирования QR кода или ввода секретного ключа вручную в 2FA-приложение, оно начинает создавать каждые 30 
   секунд новый 6-значный одноразовый код.
4. 6-значный одноразовый код необходимо ввести в соответствующее поле при входе в VeiL Broker.

!!! note "Примечание" 
    Одноразовые коды создаются на основе секретного ключа, а также текущего времени, округленного до 30 секунд 
    (алгоритм OATH TOTP — Time-based One-time Password)).