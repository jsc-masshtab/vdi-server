
// import { environment } from 'src/environments/environment';
import { Observable, ReplaySubject } from 'rxjs';
import { Injectable } from '@angular/core';


@Injectable({
  providedIn: 'root',
})

export class WebsocketService  {

  private ws: WebSocket;
  private stream_create_pool$$: ReplaySubject<string> = new ReplaySubject<string>();

  constructor() {}

  public init(): void {
    let url = `ws://192.168.20.110:8888/subscriptions`;

    this.ws = new WebSocket(url);
    if (this.ws) {
      this.ws.addEventListener<'open'>('open', this.onListenOpen.bind(this));
      this.ws.addEventListener<'message'>('message', this.onListenMessage.bind(this));
      this.ws.addEventListener<'close'>('close', this.onListenClose.bind(this));
      this.ws.addEventListener<'error'>('error', this.onListenError.bind(this));
    }
  }

  private onListenOpen(event: Event): void {
    console.log(event, 'соединение установлено');
    this.ws.send('add /vdi_tasks/');
  }

  private onListenMessage(event: MessageEvent): void {
    console.log(event.data, 'event.data ws');
    this.stream_create_pool$$.next(event.data);
  }

  public onListenClose(event?: CloseEvent): void {
    console.log(event, 'close ws');
    this.ws.close();
  }

  private onListenError(event: Event): void {
    console.log(event, 'error ws');
  }

  public getMsgCreateVMPoll(): Observable<string> {
    return this.stream_create_pool$$.asObservable();
  }
}
