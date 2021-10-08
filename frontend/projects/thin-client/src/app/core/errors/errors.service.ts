import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class ErrorsService  {

    constructor() {}

    public errors$: Subject<any> = new Subject<any>();

    public getErrors(): Observable<any> {
      return this.errors$.asObservable();
    }

    public setError(item: any): void {      
      this.errors$.next(item);
    }
}
