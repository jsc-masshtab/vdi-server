import { WebsocketPoolService } from './websockPool.service';
// import { environment } from 'src/environments/environment';
import { Injectable } from '@angular/core';


@Injectable({
  providedIn: 'root',
})

export class WebsocketService  {

  private ws: WebSocket;

  constructor(private ws_create_pool_service: WebsocketPoolService) {}

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
    this.ws_create_pool_service.setMsg(event.data);
  }

  public onListenClose(event?: CloseEvent): void {
    this.ws_create_pool_service.setComplete();
    this.ws.close();
    console.log(event, 'close');
  }

  private onListenError(event: Event): void {
    this.ws_create_pool_service.setError(event);
    console.log(event, 'error');
  }
}
