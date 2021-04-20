
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'poolType' })
export class PoolTypePipe implements PipeTransform {

    constructor() { }

    transform(poolType) {
        let translatePoolTypePipe = '';
        if (poolType === 'AUTOMATED') {
            translatePoolTypePipe = 'Автоматический';
        } else if (poolType === 'GUEST') {
            translatePoolTypePipe = 'Гостевой';
        } else if (poolType === 'STATIC') {
            translatePoolTypePipe = 'Статический';
        } else {
            translatePoolTypePipe = poolType;
        }
        return translatePoolTypePipe;
    }
}
