import { Observable, Subject } from 'rxjs';
import { Injectable } from '@angular/core';

@Injectable()
export class PoolsUpdateService  {

    constructor() {}

    public poolsUpdate$: Subject<string> = new Subject<string>();

    public getUpdate(): Observable<string> {
      return this.poolsUpdate$.asObservable();
    }

    public setUpdate(item: 'update'): void {
      this.poolsUpdate$.next(item);
    }
}
