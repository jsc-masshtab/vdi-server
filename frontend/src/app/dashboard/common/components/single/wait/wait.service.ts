import { Observable, Subject } from 'rxjs';
import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})

export class WaitService  {

  constructor() {}

  public wait$: Subject<any> = new Subject<any>();

  public getWait(): Observable<any> {
    return this.wait$.asObservable();
  }

  public setWait(item: boolean): void {
    this.wait$.next(item);
  }
}
