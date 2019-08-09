import { Observable, ReplaySubject } from 'rxjs';
import { Injectable } from '@angular/core';

@Injectable()
export class ErrorsService  {

    constructor() {}

    public errors$: ReplaySubject<any> = new ReplaySubject<any>();

    public getErrors(): Observable<any> {
      return this.errors$.asObservable();
    }
  
    public setError(item: any): void {
      this.errors$.next(item);
    }
 
}