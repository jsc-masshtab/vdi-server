
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'status' })
export class StatusPipe implements PipeTransform {

    constructor() { }

    transform(status) {
        let translateStatus = '';
        if (status === 'CREATING') {
            translateStatus = 'создается';
        } else if (status === 'DELETING') {
            translateStatus = 'удаляется';
        } else if (status === 'ACTIVE') {
            translateStatus = 'исправно';
        } else if (status === 'BAD_AUTH') {
            translateStatus = 'ошибка авторизации';
        } else if (status === 'FAILED') {
            translateStatus = 'произошла ошибка';
        } else if (status === 'FAIL_CREATING') {
            translateStatus = 'ошибка добавления';
        } else if (status === 'FAIL_DELETING') {
            translateStatus = 'ошибка удаления';
        } else if (status === 'PENDING') {
            translateStatus = 'в очереди';
        } else if (status === 'HERMIT') {
            translateStatus = 'нет соединения';
        } else if (status === 'ERROR') {
            translateStatus = 'недоступно';
        } else if (status === 'HALTING') {
            translateStatus = 'сбой';
        } else if (status === 'STARTING' || status === 'INITIAL') {
            translateStatus = 'запускается';
        } else if (status === 'REJECTED') {
            translateStatus = 'отклонено';
        } else if (status === 'IN_PROGRESS') {
            translateStatus = 'выполняется';
        } else if (status === 'PARTIAL') {
            translateStatus = 'частично выполнено';
        } else if (status === 'TIMEOUT') {
            translateStatus = 'вышло время';
        } else if (status === 'SERVICE') {
            translateStatus = 'сервисный режим';
        } else if (status === 'RESERVED') {
            translateStatus = 'зарезервировано';
        } else if (status === 'UNDEFINED' || status === 'Unknown') {
            translateStatus = 'не найдено';
        } else if (status === 'CANCELLED') {
            translateStatus = 'отменено';
        } else if (status === 'FINISHED') {
            translateStatus = 'завершено';
        } else {
            translateStatus = status;
        }
        return translateStatus;
    }
}

