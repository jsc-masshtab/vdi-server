export class PoolStatisticsCollections {
  public collectionConnections: any[] = [
    {
      title: 'Число успешных подключений',
      property: 'successful_conn_number',
      type: 'string'
    },
    {
      title: 'Число отключений',
      property: 'disconn_number',
      type: 'string'
    },
    {
      title: 'Число неудачных подключений',
      property: 'conn_err_number',
      type: 'string'
    },
    {
      title: 'Средняя продолжительность подключения',
      property: 'conn_duration_average',
      type: 'string'
    }
  ]

  public collectionErrors: any[] = [
    {
      title: 'Текст ошибки',
      property: 'name',
      type: 'string',
      class: 'name-start'
    },
    {
      title: 'Число неудачных подключений',
      property: 'conn_number',
      type: 'string'
    }
  ]

  public titles = {
    successful_conn_number: 'Число успешных подключений к пулу',
    disconn_number: 'Число отключений от пула',
    conn_err_number: 'Число неудачных подключений к пулу',
    conn_duration_average: 'Средняя продолжительность подключения к пулу(ВМ)',

    used_pools_overall: 'Топ пулов по количеству подключений',
    used_client_os: 'Топ используемых ОС тонкими клиентами',
    used_client_versions: 'Топ используемых версий ПО тонких клиентов',
    users: 'Топ пользователей с наибольшим числом подключением',

    conn_errors: 'Топ ошибок подключения к пулам по количеству', 

    conn_number_by_time_interval: 'Данные о числе подключений по интервалам дня',
    time_interval: 'Интервал', 
    conn_number: 'Количество подключений',
    percentage: 'Процент от общего числа подключений для данного интервала'
  }
}
