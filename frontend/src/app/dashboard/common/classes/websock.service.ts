import { Observable, ReplaySubject } from 'rxjs';
import { Injectable } from '@angular/core';
import { AuthStorageService } from 'src/app/login/authStorage.service';

import { environment } from 'src/environments/environment';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root',
})

export class WebsocketService  {

  timeout: any;

  private ws: WebSocket;
  private stream_create_pool$$: ReplaySubject<string> = new ReplaySubject<string>();

  constructor(
    private authStorageService: AuthStorageService,
    private router: Router
  ) {}

  public init(): void {
    const host = window.location.host;
    const prot = window.location.protocol;
    const api_ws = environment.api_ws;
    const token = this.authStorageService.getItemStorage('token');

    if (token) {
      let url = `ws://${host}/${api_ws}ws/subscriptions/?token=jwt ${token}`;

      if (prot == 'https:') {
        url = `wss://${host}/${api_ws}ws/subscriptions/?token=jwt ${token}`;
      }

      this.ws = new WebSocket(url);
    } else {
      this.ws.close()
      this.router.navigate(['login']);
    }
    
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

  private onListenClose(event: CloseEvent): void {
    console.log(event, 'close ws');
  }

  private onListenError(event: Event): void {
    console.log(event, 'error ws');

    if (this.timeout) {
      clearTimeout(this.timeout);
    }

    this.timeout = setTimeout(() => {
      this.init()
    }, 5000)
  }

  public close() {
    this.ws.close();
  }

  public getMsgCreateVMPoll(): Observable<string> {
    return this.stream_create_pool$$.asObservable();
  }
}
