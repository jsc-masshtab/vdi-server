
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
        } else if (status === 'STARTING') {
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
        } else {
            translateStatus = status;
        }
        return translateStatus;
    }
}

@Pipe({ name: 'statusIcon' })
export class StatusIconPipe implements PipeTransform {
    constructor() {}

    transform(status) {
        let translateStatus = '';
        switch (status) {
            case 'FAILED':
            case 'FAIL_CREATING':
            case 'FAIL_DELETING':
            case 'ERROR':
            case 'REJECTED':
            case 'PARTIAL':
            case 'TIMEOUT':
            case 'BAD_AUTH':
            translateStatus = 'exclamation-triangle';
            break;

            case 'CREATING':
            case 'DELETING':
            case 'PENDING':
            case 'HERMIT':
            case 'STARTING':
            case 'IN_PROGRESS':
            translateStatus = 'spinner';
            break;

            case 'ACTIVE':
            translateStatus = 'check-square';
            break;

            case 'HALTING':
            case 'UNDEFINED':
            case 'Unknown':
            translateStatus = 'question-circle';
            break;

            case 'SERVICE':
            translateStatus = 'heartbeat';
            break;

            case 'RESERVED':
            translateStatus = 'user';
            break;

            default:
            translateStatus = 'check-square';
        }
        return translateStatus;
    }

}
