import { environment } from 'src/environments/environment';
import { Injectable } from '@angular/core';


@Injectable()
export class WebsocketService  {

  private ws: WebSocket;

  public init(): void {
    let url = `ws://${environment.url_ws}/subscriptions`;

    this.ws = new WebSocket(url);
    if (this.ws) {
      this.open();
      this.streamMessage();
      this.close();
      this.error();
    }
  }

  public open(): void {
    this.ws.addEventListener<'open'>('open', this.onListenOpen.bind(this));
  }

  public streamMessage(): void {
    this.ws.addEventListener<'message'>('message', this.onListenMessage.bind(this));
  }

  public close(): void {
    this.ws.addEventListener<'close'>('close', this.onListenClose.bind(this));
  }

  public error(): void {
    this.ws.addEventListener<'error'>('error', this.onListenError.bind(this));
  }

  private onListenOpen(event: Event): void {
    console.log(event, 'соединение установлено');
    this.ws.send('add /vdi_tasks/');
  }

  private onListenMessage(event: MessageEvent): void {
    console.log(event.data, 'msg');
  }

  private onListenClose(event: CloseEvent): void {
    console.log(event, 'close');
  }

  private onListenError(event: Event): void {
    console.log(event, 'error');
  }
}
