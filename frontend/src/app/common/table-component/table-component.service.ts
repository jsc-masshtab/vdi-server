import { Observable, Subject } from 'rxjs';
import { Injectable } from '@angular/core';

@Injectable()
export class TableService  {

    constructor() {}

    public activeSpinner$: Subject<any> = new Subject<any>();

    public getStateSpinner(): Observable<any> {
      return this.activeSpinner$.asObservable();
    }
  
    public setStateSpinner(item: any): void {
      this.activeSpinner$.next(item);
    }
 
}