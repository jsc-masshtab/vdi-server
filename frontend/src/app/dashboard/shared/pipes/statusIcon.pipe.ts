import { Pipe, PipeTransform } from '@angular/core';

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
