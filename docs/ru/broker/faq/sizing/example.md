# Пример расчета количества ВМ на сервер

В таблице приведен пример расчета количества ВМ при коэффициенте переподписки CPU равном 4 с резервированием 15% ресурсов.

| Сервер                 | 2*Silver 4215R (8С 3.20GHz) 256 Gb |2*Gold 5115 (10C 2.40GHz) 256 Gb RAM | 2*Gold 6226(12C 2.70GHz) 512Gb RAM |2*Gold 4214 (12C 2.20GHz) 512Gb RAM | 2*Gold 6132(14C 2.6Ghz) 512Gb RAM | ２*Gold 6242(16C 2.80GHz) 512Gb RAM |2*Gold 6230 (20C 2.10GHz) 512Gb RAM | 2*Gold 5220R(24С 2.20GHz) 512Gb RAM |
|:-----------------------|:----------------------------------:|:-----------------------------------:|:----------------------------------:|:----------------------------------:|:---------------------------------:|:-----------------------------------:|:-----------------------------------:|:-----------------------------------:|
| vCPU max               | 108                                | 120                                 | 163                                | 163                                | 190                               |217                                  |272                                  |326                                  |
| RAM max                | 217                                | 217                                 | 435                                | 435                                | 435                               |435                                  |435                                  |435                                  |
| Тип 1                  | 37                                 | 42                                  | 59                                 | 59                                 | 70                                |81                                   |102                                  |124                                  |
| Тип 1                  | 37                                 | 42                                  | 59                                 | 59                                 | 70                                |81                                   |102                                  |108*                                  |
| Тип 2                  | 21                                 | 23                                  | 33                                 | 33                                 | 39                                |45                                   |57                                   |69                                   |
| Тип 3                  | 21                                 | 23                                  | 33                                 | 33                                 | 39                                |45                                   |54*                                   |54*                                   |
| Тип 4                  | 11                                 | 12                                  | 17                                 | 17                                 | 21                                |24                                   |30                                   |37                                   |
| Тип 6                  | 11                                 | 12                                  | 17                                 | 17                                 | 21                                |24                                   |27*                                   |27*                                   |

\* - Упор в объем RAM

!!! attention "Внимание"
    Приведенном в таблице примере расчета не учитывается избыточность необходимая для функционирования механизма **Высокой Доступности**. 