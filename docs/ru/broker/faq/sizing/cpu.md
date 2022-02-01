# Расчет CPU

Рекомендуемые количество **vCPU** и **коэффициент переподписки vCPU:CPU** для предлагаемых профилей использования содержатся в разделе [Профили использования](profiles.md).

## Количество**vCPU**на одну ВМ

Определение необходимого количества выделяемых одной ВМ **vCPU** должно производится исходя из системных требований предъявляемых к ОС и используемому программному обеспечению, и по результатам анализа рабочих нагрузок пользователей.

Анализ реального потребления вычислительных ресурсов рекомендуется  проводить с использованием ПО мониторинга. Такой анализ может быть выполнен для каждой типовой группы сотрудников при выполнении ими типичных рабочих задач с использованием ОС и программного обеспечения, которое планируется использовать в инфраструктуре удаленных рабочих столов.

## Коэффициент переподписки vCPU:CPU

Количество выделенных **vCPU** включенным ВМ может быть больше, чем имеющееся количество **CPU** (количество потоков) в кластере. Соотношение числа выделенных виртуальным машинам **vCPU** к общему количеству **CPU** называется **коэффициент переподписки vCPU:CPU** и считается по формуле ```vCPU/CPU```. 


Выбирать коэффициент переподписки при проектировании следует с осторожностью, отталкиваясь от специфики выполняемых задач.
Предположим, что для группы пользователей ситуация когда более 25% пользователей, одновременно выполняют ресурсоемкие операции требующие 100% вычислительной мощности ВМ, является нетипичной, и вероятность ее возникновения стремится к нулю. Тогда, при проектировании VDI допустимо использовать коэффициент переподписки **vCPU:СPU** равный 4. Это позволит увеличить максимально возможное количество пользователей, или сократить физическое количество CPU в четыре раза, по сравнению с вариантом без  переподписки. 
Однако, если для группы пользователей типична ситуация, когда большинство пользователей выполняет ресурсоемкие операции в течении всего рабочего дня, и все ВМ задействованы постоянно с загрузкой **vCPU** 50% и выше, то будет правильным уменьшить коэффициент переподписки **vCPU:СPU** до 2 или менее (если загрузка **vCPU**>50%), или вовсе принять равным единице. 

Для определения подходящего **коэффициента переподписки vCPU:CPU** стоит провести анализ активности пользователей и среднего количества одновременного выполнения задач связанных с высокими нагрузками на CPU.

!!! info "vGPU"
    Для ВМ с vGPU следует использовать **коэффициент переподписки vCPU:CPU** не более 2. Подробная информация содержится в разделе [Рекомендации к использованию vGPU](grid.md).

## Использование групп ВМ с разным коэффициентом переподписки vCPU:CPU

Для разделения групп пользователей с разными **коэффициентами переподписки vCPU:CPU** следует использовать отдельные пулы ресурсов в ECP Veil.