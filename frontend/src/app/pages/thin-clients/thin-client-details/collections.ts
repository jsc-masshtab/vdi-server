export class ThinClientColections { 
  public collection: object[] = [
    {
      title: 'IP адрес',
      property: 'tk_ip',
      type: 'string'
    },
    {
      title: 'Операционная система',
      property: 'tk_os',
      type: 'string'
    },
    {
      title: 'Версия',
      property: 'veil_connect_version',
      type: 'string'
    },
    {
      title: 'Пользователь',
      property: 'user_name',
      type: 'string'
    },
    {
      title: 'Время подключения',
      property: 'connected',
      type: 'time'
    },
    {
      title: 'Время отключения',
      property: 'disconnected',
      type: 'time'
    },
    {
      title: 'Время получения данных',
      property: 'data_received',
      type: 'time'
    },
    {
      title: 'Время последней активности',
      property: 'last_interaction',
      type: 'time'
    },
    {
      title: 'Статус активности',
      property: 'is_afk',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Не активен', 'Активен']
      }
    },
    {
      title: 'Mac адрес',
      property: 'mac_address',
      type: 'string'
    },
    {
      title: 'Имя хоста',
      property: 'hostname',
      type: 'string'
    }
  ];

  public vm_collection: object[] = [
    {
      title: 'Виртуальная машина',
      property: 'vm_name',
      type: 'string'
    },
    {
      title: 'Тип подключения',
      property: 'connection_type',
      type: 'string'
    },
    {
      title: 'Использование TLS',
      property: 'is_connection_secure',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['да', '--']
      }
    },
    {
      title: 'Скорость получения данных',
      property: 'read_speed',
      type: 'metric',
      unit: '/с'
    },
    {
      title: 'Скорость отправки данных',
      property: 'write_speed',
      type: 'metric',
      unit: '/с'
    },
    {
      title: 'Средний RTT',
      property: 'avg_rtt',
      type: 'number',
      unit: 'мс'
    },
    {
      title: 'Процент сетевых потерь',
      property: 'loss_percentage',
      type: 'number',
      unit: '%'
    }
  ]
}
