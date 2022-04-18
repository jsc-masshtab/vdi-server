export class PoolCollections {
  public collectionDetailsStatic: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string',
      edit: 'changeName'
    },
    {
      title: 'Тип',
      property: 'pool_type',
      type: 'pool_type'
    },
    {
      title: 'Тип подключения пула',
      property: 'assigned_connection_types',
      type: 'string',
      edit: 'changeConnectionType'
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Адрес контроллера',
      property: 'controller',
      property_lv2: 'address'
    },
    {
      title: 'Пул ресурсов',
      property: 'resource_pool',
      property_lv2: 'verbose_name',
    },
    {
      title: 'Действия над ВМ после отключения пользователя',
      edit: 'manageVm',
      group: [
        {
          title: 'Освобождать ВМ от пользователя',
          property: 'free_vm_from_user',
          type: {
            typeDepend: 'boolean',
            propertyDepend: ['Да', 'Нет']
          }
        },
        {
          title: 'Действие',
          property: 'vm_action_upon_user_disconnect',
          type: 'vmAction'
        },
        {
          title: 'Таймаут',
          property: 'vm_disconnect_action_timeout',
          type: 'vm_disconnect_action_timeout'
        }
      ]
    },
    {
      title: 'Всего ВМ',
      property: 'vms',
      type: 'array-length'
    },
    {
      title: 'Пользователи',
      property: 'users',
      type: 'array-length'
    },
    {
      title: 'Статус',
      property: 'status',
      type: 'string'
    },
  ];

  public collectionDetailsRds: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string',
      edit: 'changeName'
    },
    {
      title: 'Тип',
      property: 'pool_type',
      type: 'pool_type'
    },
    {
      title: 'Тип подключения пула',
      property: 'assigned_connection_types',
      type: 'string',
      edit: 'changeConnectionType'
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Адрес контроллера',
      property: 'controller',
      property_lv2: 'address'
    },
    {
      title: 'Пул ресурсов',
      property: 'resource_pool',
      property_lv2: 'verbose_name',
    },
    {
      title: 'Всего ВМ',
      property: 'vms',
      type: 'array-length'
    },
    {
      title: 'Пользователи',
      property: 'users',
      type: 'array-length'
    },
    {
      title: 'Статус',
      property: 'status',
      type: 'string'
    },
  ];

  public collectionDetailsAutomated: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string',
      edit: 'changeName'
    },
    {
      title: 'Тип',
      property: 'pool_type',
      type: 'pool_type'
    },
    {
      title: 'Тип подключения пула',
      property: 'assigned_connection_types',
      type: 'string',
      edit: 'changeConnectionType'
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Адрес контроллера',
      property: 'controller',
      property_lv2: 'address'
    },
    {
      title: 'Тонкие клоны',
      property: 'create_thin_clones',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Создаются', 'Не создаются']
      },
      edit: 'changeAutomatedPoolCreate_thin_clones'
    },
    {
      title: 'Держать ВМ с пользователями включенными',
      property: 'keep_vms_on',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Да', 'Нет']
      },
      edit: 'changeAutomatedPoolKeep_vms_on'
    },
    {
      title: 'Действия над ВМ после отключения пользователя',
      edit: 'manageVm',
      group: [
        {
          title: 'Освобождать ВМ от пользователя',
          property: 'free_vm_from_user',
          type: {
            typeDepend: 'boolean',
            propertyDepend: ['Да', 'Нет']
          }
        },
        {
          title: 'Действие',
          property: 'vm_action_upon_user_disconnect',
          type: 'vmAction'
        },
        {
          title: 'Таймаут',
          property: 'vm_disconnect_action_timeout',
          type: 'vm_disconnect_action_timeout'
        }
      ]
    },
    {
      title: 'Пул ресурсов',
      property: 'resource_pool',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Пул данных',
      property: 'datapool',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Шаблон ВМ',
      property: 'template',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Начальное количество ВМ',
      property: 'initial_size',
      type: 'string'
    },
    {
      title: 'Шаг расширения пула',
      property: 'increase_step',
      type: 'string',
      edit: 'changeAutomatedPoolIncreaseStep'
    },
    {
      title: 'Максимальное количество создаваемых ВМ',
      // Максимальное количество ВМ в пуле -  c тонкого клиента вм будут создаваться
      // с каждым подключ. пользователем даже,если рес-сы закончатся
      property: 'total_size',
      type: 'string',
      edit: 'changeMaxAutomatedPool'
    },
    {
      title: 'Пороговое количество свободных ВМ',
      property: 'reserve_size',
      type: 'string',
      edit: 'changeAutomatedPoolReserveSize'
    },
    {
      title: 'Количество доступных ВМ',
      property: 'vms',
      type: 'array-length'
    },
    {
      title: 'Шаблон для имени ВМ',
      property: 'vm_name_template',
      type: 'string',
      edit: 'changeTemplateForVmAutomatedPool'
    },
    {
      title: 'Подготавливать ВМ',
      edit: 'changeAutomatedPoolPrepare_vms',
      group: [
        {
          title: 'Включать удаленный доступ на ВМ',
          property: 'enable_vms_remote_access',
          type: {
            typeDepend: 'boolean',
            propertyDepend: ['Да', 'Нет']
          }
        },
        {
          title: 'Включать ВМ',
          property: 'start_vms',
          type: {
            typeDepend: 'boolean',
            propertyDepend: ['Да', 'Нет']
          }
        },
        {
          title: 'Задавать hostname ВМ',
          property: 'set_vms_hostnames',
          type: {
            typeDepend: 'boolean',
            propertyDepend: ['Да', 'Нет']
          }
        },
        {
          title: 'Вводить ВМ в домен',
          property: 'include_vms_in_ad',
          type: {
            typeDepend: 'boolean',
            propertyDepend: ['Да', 'Нет']
          }
        }
      ]
    },
    {
      title: 'Наименование организационной единицы для добавления ВМ в AD',
      property: 'ad_ou',
      type: 'string',
      edit: 'changeAdCnPatternForGroupAutomatedPool'
    },
    {
      title: 'Пользователи',
      property: 'users',
      type: 'array-length'
    },
    {
      title: 'Статус',
      property: 'status',
      type: 'string'
    }
  ];

  public collectionDetailsGuest: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string',
      edit: 'changeName'
    },
    {
      title: 'Тип',
      property: 'pool_type',
      type: 'pool_type'
    },
    {
      title: 'Тип подключения пула',
      property: 'assigned_connection_types',
      type: 'string',
      edit: 'changeConnectionType'
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Адрес контроллера',
      property: 'controller',
      property_lv2: 'address'
    },
    {
      title: 'Тонкие клоны',
      property: 'create_thin_clones',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Создаются', 'Не создаются']
      }
    },
    {
      title: 'Держать ВМ с пользователями включенными',
      property: 'keep_vms_on',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Да', 'Нет']
      },
      edit: 'changeAutomatedPoolKeep_vms_on'
    },
    {
      title: 'Время жизни ВМ после потери связи',
      property: 'vm_disconnect_action_timeout',
      type: 'vm_disconnect_action_timeout',
      edit: 'changeGuestPoolWaitingTime'
    },
    {
      title: 'Пул ресурсов',
      property: 'resource_pool',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Пул данных',
      property: 'datapool',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Шаблон ВМ',
      property: 'template',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Начальное количество ВМ',
      property: 'initial_size',
      type: 'string'
    },
    {
      title: 'Шаг расширения пула',
      property: 'increase_step',
      type: 'string',
      edit: 'changeAutomatedPoolIncreaseStep'
    },
    {
      title: 'Максимальное количество создаваемых ВМ',
      property: 'total_size',
      type: 'string',
      edit: 'changeMaxAutomatedPool'
    },
    {
      title: 'Пороговое количество свободных ВМ',
      property: 'reserve_size',
      type: 'string',
      edit: 'changeAutomatedPoolReserveSize'
    },
    {
      title: 'Количество доступных ВМ',
      property: 'vms',
      type: 'array-length'
    },
    {
      title: 'Шаблон для имени ВМ',
      property: 'vm_name_template',
      type: 'string',
      edit: 'changeTemplateForVmAutomatedPool'
    },
    {
      title: 'Подготавливать ВМ',
      group: [
        {
          title: 'Включать удаленный доступ на ВМ',
          property: 'enable_vms_remote_access',
          type: {
            typeDepend: 'boolean',
            propertyDepend: ['Да', 'Нет']
          }
        },
        {
          title: 'Включать ВМ',
          property: 'start_vms',
          type: {
            typeDepend: 'boolean',
            propertyDepend: ['Да', 'Нет']
          }
        }
      ]
    },
    {
      title: 'Пользователи',
      property: 'users',
      type: 'array-length'
    },
    {
      title: 'Статус',
      property: 'status',
      type: 'string'
    }
  ];

  public collectionVmsAutomated: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'desktop',
      type: 'string',
      sort: true
    },
    {
      title: 'Шаблон',
      property: 'parent_name',
      type: 'string',
      sort: true
    },
    {
      title: 'Пользователи',
      property: 'assigned_users',
      type: 'users-array'
    },
    {
      title: 'Статус',
      property: 'status',
      sort: true
    },
    {
      title: 'Гостевой агент',
      property: 'qemu_state',
      type: 'string',
      sort: true
    }
  ];

  public collectionVmsGuest: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'desktop',
      type: 'string',
      sort: true
    },
    {
      title: 'Шаблон',
      property: 'parent_name',
      type: 'string',
      sort: true
    },
    {
      title: 'Пользователи',
      property: 'assigned_users',
      type: 'users-array'
    },
    {
      title: 'Статус',
      property: 'status',
      sort: true
    },
    {
      title: 'Гостевой агент',
      property: 'qemu_state',
      type: 'string',
      sort: true
    }
  ];

  public collectionVmsStatic: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'desktop',
      type: 'string',
      sort: true
    },
    {
      title: 'Пользователи',
      property: 'assigned_users',
      type: 'users-array'
    },
    {
      title: 'Статус',
      property: 'status',
      sort: true
    },
    {
      title: 'Гостевой агент',
      property: 'qemu_state',
      type: 'string',
      sort: true
    }
  ];

  public collectionVmsRds: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'desktop',
      type: 'string',
      sort: true
    },
    {
      title: 'Статус',
      property: 'status',
      sort: true
    },
    {
      title: 'Гостевой агент',
      property: 'qemu_state',
      type: 'string',
      sort: true
    }
  ];

  public collectionUsers: any[] = [
    {
      title: 'Имя пользователя',
      property: 'username',
      class: 'name-start',
      icon: 'user',
      type: 'string',
      sort: true
    }
  ];

  public collectionEventVm: any[] = [
    {
      title: 'Событие',
      property: 'msg',
      class: 'name-start',
      icon: 'comment',
      type: 'string'
    }
  ];

  public collectionGroups: object[] = [
    {
      title: 'Название группы',
      type: 'string',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'users-cog',
      sort: true
    }
  ];
}
