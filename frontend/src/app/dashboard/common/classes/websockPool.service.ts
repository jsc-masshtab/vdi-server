import { Observable, ReplaySubject } from 'rxjs';
import { Injectable } from '@angular/core';

@Injectable()
export class WebsocketPoolService  {

    constructor() {}

    private stream_create_pool$$: ReplaySubject<string> = new ReplaySubject<string>();

    public getMsg(): Observable<string> {
      return this.stream_create_pool$$.asObservable();
    }

    public setMsg(msg: string): void {
      console.log(msg);
      this.stream_create_pool$$.next(msg);
    }

    public setError(msg: any): void {
      this.stream_create_pool$$.error(msg);
    }

    public setComplete(): void {
      this.stream_create_pool$$.complete();
    }
}
