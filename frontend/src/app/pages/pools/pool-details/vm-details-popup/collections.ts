export class VmCollections {
  public collectionIntoVmAutomated: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string'
    },
    {
      title: 'Описание',
      property: 'description',
      type: 'string'
    },
    {
      title: 'Состояние',
      property: 'user_power_state',
      type: 'string'
    },
    {
      title: 'IP адрес',
      property: 'address',
      type: 'array'
    },
    {
      title: 'Имя хоста',
      property: 'hostname',
      type: 'string'
    },
    {
      title: 'Процессоры',
      property: 'cpu_count',
      type: 'string'
    },
    {
      title: 'Оперативная память',
      property: 'memory_count',
      type: 'bites',
      delimiter: 'Мб'
    },
    {
      title: 'Операционная система',
      property: 'os_type',
      type: 'string'
    },
    {
      title: 'Версия операционной системы',
      property: 'os_version',
      type: 'string'
    },
    {
      title: 'Шаблон',
      property: 'parent_name',
      type: 'string'
    },
    {
      title: 'Пул ресурсов',
      property: 'resource_pool',
      property_lv2: 'verbose_name',
      type: 'string'
    },
    {
      property: 'tablet',
      title: 'Режим планшета',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'spice_stream',
      title: 'SPICE потоки',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'ha_enabled',
      title: 'Высокая доступность',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'disastery_enabled',
      title: 'Катастрофоустойчивость',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'guest_agent',
      title: 'Гостевой агент',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'remote_access',
      title: 'Удаленный доступ',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'start_on_boot',
      title: 'Автоматический запуск ВМ',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      title: 'Тип загрузочного меню',
      property: 'boot_type',
      type: 'string'
    },
    {
      title: 'Статус',
      property: 'status',
      type: 'string'
    },
    {
      title: 'Тэги',
      property: 'domain_tags',
      type: {
        typeDepend: 'tags_array'
      }
    }
  ];

  public collectionIntoVmGuest: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string'
    },
    {
      title: 'Описание',
      property: 'description',
      type: 'string'
    },
    {
      title: 'Состояние',
      property: 'user_power_state',
      type: 'string'
    },
    {
      title: 'IP адрес',
      property: 'address',
      type: 'array'
    },
    {
      title: 'Имя хоста',
      property: 'hostname',
      type: 'string'
    },
    {
      title: 'Процессоры',
      property: 'cpu_count',
      type: 'string'
    },
    {
      title: 'Оперативная память',
      property: 'memory_count',
      type: 'bites',
      delimiter: 'Мб'
    },
    {
      title: 'Операционная система',
      property: 'os_type',
      type: 'string'
    },
    {
      title: 'Версия операционной системы',
      property: 'os_version',
      type: 'string'
    },
    {
      title: 'Шаблон',
      property: 'parent_name',
      type: 'string'
    },
    {
      title: 'Пул ресурсов',
      property: 'resource_pool',
      property_lv2: 'verbose_name',
      type: 'string'
    },
    {
      property: 'tablet',
      title: 'Режим планшета',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'spice_stream',
      title: 'SPICE потоки',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'ha_enabled',
      title: 'Высокая доступность',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'disastery_enabled',
      title: 'Катастрофоустойчивость',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'guest_agent',
      title: 'Гостевой агент',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'remote_access',
      title: 'Удаленный доступ',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'start_on_boot',
      title: 'Автоматический запуск ВМ',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      title: 'Тип загрузочного меню',
      property: 'boot_type',
      type: 'string'
    },
    {
      title: 'Статус',
      property: 'status',
      type: 'string'
    },
    {
      title: 'Тэги',
      property: 'domain_tags',
      type: {
        typeDepend: 'tags_array'
      }
    }
  ];

  public collectionIntoVmStatic: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string'
    },
    {
      title: 'Описание',
      property: 'description',
      type: 'string'
    },
    {
      title: 'Состояние',
      property: 'user_power_state',
      type: 'string'
    },
    {
      title: 'IP адрес',
      property: 'address',
      type: 'array'
    },
    {
      title: 'Имя хоста',
      property: 'hostname',
      type: 'string'
    },
    {
      title: 'Процессоры',
      property: 'cpu_count',
      type: 'string'
    },
    {
      title: 'Оперативная память',
      property: 'memory_count',
      type: 'bites',
      delimiter: 'Мб'
    },
    {
      title: 'Операционная система',
      property: 'os_type',
      type: 'string'
    },
    {
      title: 'Версия операционной системы',
      property: 'os_version',
      type: 'string'
    },
    {
      title: 'Шаблон',
      property: 'parent_name',
      type: 'string'
    },
    {
      title: 'Пул ресурсов',
      property: 'resource_pool',
      property_lv2: 'verbose_name',
      type: 'string'
    },
    {
      property: 'tablet',
      title: 'Режим планшета',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'spice_stream',
      title: 'SPICE потоки',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'ha_enabled',
      title: 'Высокая доступность',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'disastery_enabled',
      title: 'Катастрофоустойчивость',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'guest_agent',
      title: 'Гостевой агент',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'remote_access',
      title: 'Удаленный доступ',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'start_on_boot',
      title: 'Автоматический запуск ВМ',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      title: 'Тип загрузочного меню',
      property: 'boot_type',
      type: 'string'
    },
    {
      title: 'Статус',
      property: 'status',
      type: 'string'
    },
    {
      title: 'Тэги',
      property: 'domain_tags',
      type: {
        typeDepend: 'tags_array'
      }
    }
  ];

  public collectionIntoVmRds: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string'
    },
    {
      title: 'Описание',
      property: 'description',
      type: 'string'
    },
    {
      title: 'Состояние',
      property: 'user_power_state',
      type: 'string'
    },
    {
      title: 'IP адрес',
      property: 'address',
      type: 'array'
    },
    {
      title: 'Имя хоста',
      property: 'hostname',
      type: 'string'
    },
    {
      title: 'Процессоры',
      property: 'cpu_count',
      type: 'string'
    },
    {
      title: 'Оперативная память',
      property: 'memory_count',
      type: 'bites',
      delimiter: 'Мб'
    },
    {
      title: 'Операционная система',
      property: 'os_type',
      type: 'string'
    },
    {
      title: 'Версия операционной системы',
      property: 'os_version',
      type: 'string'
    },
    {
      title: 'Шаблон',
      property: 'parent_name',
      type: 'string'
    },
    {
      title: 'Пул ресурсов',
      property: 'resource_pool',
      property_lv2: 'verbose_name',
      type: 'string'
    },
    {
      property: 'tablet',
      title: 'Режим планшета',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'spice_stream',
      title: 'SPICE потоки',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'ha_enabled',
      title: 'Высокая доступность',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'disastery_enabled',
      title: 'Катастрофоустойчивость',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'guest_agent',
      title: 'Гостевой агент',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'remote_access',
      title: 'Удаленный доступ',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'start_on_boot',
      title: 'Автоматический запуск ВМ',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      title: 'Тип загрузочного меню',
      property: 'boot_type',
      type: 'string'
    },
    {
      title: 'Статус',
      property: 'status',
      type: 'string'
    },
    {
      title: 'Тэги',
      property: 'domain_tags',
      type: {
        typeDepend: 'tags_array'
      }
    }
  ];

  public collectionVmConnections: any[] = [
    {
      title: 'Протокол',
      property: 'connection_type',
      type: 'string'
    },
    {
      title: 'Адрес',
      property: 'address',
      type: 'string'
    },
    {
      title: 'Порт',
      property: 'port',
      type: 'string'
    },
    {
      title: 'Статус',
      property: 'active',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      title: 'Действия',
      type: 'buttons',
      buttons: [
        {
          title: 'Удалить',
          icon: 'trash-alt',
          action: 'removeVmConnection'
        }
      ]
    },
  ];

  public collectionUsers: any[] = [
    {
      title: 'Пользователь',
      property: 'username',
      class: 'name-start',
      type: 'string',
      icon: 'user'
    }
  ];

  public collectionEvents: object[] = [
    {
      title: 'Сообщение',
      property: 'message',
      class: 'name-start',
      type: 'string',
      icon: 'comment'
    },
    {
      title: 'Cоздатель',
      property: 'user',
      type: 'string',
      class: 'name-end',
      // sort: true
    },
    {
      title: 'Дата создания',
      property: 'created',
      type: 'time',
      class: 'name-end',
      // sort: true
    }
  ];

  public collectionBackups: object[] = [
    {
      title: 'Название',
      property: 'filename',
      class: 'name-start',
      type: 'string',
      icon: 'file-archive'
    },
    {
      title: 'Пул данных',
      property: 'datapool',
      property_lv2: 'verbose_name',
      type: 'string'
    },
    {
      title: 'Тип',
      property: 'assignment_type',
      type: 'string'
    },
    {
      title: 'Размер',
      property: 'size',
      type: 'bites'
    },
    {
      title: 'Статус',
      property: 'status',
      type: 'string'
    },
  ];
}
