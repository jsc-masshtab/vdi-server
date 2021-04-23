
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'taskType' })
export class TaskTypePipe implements PipeTransform {

    constructor() { }

    transform(taskType) {
        let translateTaskTypePipe = '';
        if (taskType === 'POOL_CREATE') {
            translateTaskTypePipe = 'Создание пула';
        } else if (taskType === 'POOL_EXPAND') {
            translateTaskTypePipe = 'Расширение пула';
        } else if (taskType === 'POOL_DELETE') {
            translateTaskTypePipe = 'Удаление пула';
        } else if (taskType === 'POOL_DECREASE') {
            translateTaskTypePipe = 'Уменьшение пула';
        } else if (taskType === 'VM_PREPARE') {
            translateTaskTypePipe = 'Подготовка ВМ';
        } else if (taskType === 'VMS_BACKUP') {
            translateTaskTypePipe = 'Создание резервной копии ВМ';
        } else {
            translateTaskTypePipe = taskType;
        }
        return translateTaskTypePipe;
    }
}
