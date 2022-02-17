import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class FooterService {

constructor() { }
  getTime(): any {
    return of({
      time: '2022-02-17T17:44:14.834368Z',
      timezone: 'Europe/Moscow'
    })
  }
}
