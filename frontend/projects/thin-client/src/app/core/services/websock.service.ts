import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { Subject, Observable, Subscription } from 'rxjs';

import { AuthStorageService } from './authStorage.service';
import { environment } from 'environments/environment';
import { filter } from 'rxjs/operators';



@Injectable({
  providedIn: 'root',
})

export class WebsocketService {

  timeout: any;
  private connections: any = {};

  private ws: WebSocket;

  private event  = new Subject();
  event$ = this.event.asObservable();

  constructor(
    private authStorageService: AuthStorageService,
    private router: Router
  ) { }

  public init(vmId: string | null): void {
    const host = window.location.host;
    const prot = window.location.protocol;
    const api_ws = environment.api_ws;
    const token = this.authStorageService.getItemStorage('token');

    if (token) {
      let url = `ws://${host}/${api_ws}ws/client/?token=jwt ${token}&is_conn_init_by_user=1&veil_connect_version=1.5.2&tk_os=Linux&vm_id=${vmId}`;

      if (prot === 'https:') {
        url = `wss://${host}/${api_ws}ws/client/?token=jwt ${token}&is_conn_init_by_user=1&veil_connect_version=1.5.2&tk_os=Linux&vm_id=${vmId}`;
      }

      this.ws = new WebSocket(url);
    } else {
      this.ws.close();
      this.router.navigate(['login']);
    }

    if (this.ws) {
      this.ws.addEventListener<'open'>('open', this.onListenOpen.bind(this));
      this.ws.addEventListener<'message'>('message', (e) => (this.onListenMessage(e)));
      this.ws.addEventListener<'close'>('close',  (e) => (this.onListenClose(e, vmId)));
      this.ws.addEventListener<'error'>('error', (e) => (this.onListenError(e, vmId)));
    }
  }

  public stream(listener) {

    this.connect(listener);

    return new Observable(observer => {

      let sub: Subscription;

      sub = this.event$
        .pipe(filter((ws: any) => ws.resource === listener))
        .subscribe((message: any) => observer.next(message));

      return () => {
        this.disconnect(listener);

        if (sub) {
          observer.unsubscribe();
        }
      };
    });
  }

  private isJsonString(str) {
    try {
      JSON.parse(str);
    } catch (e) {
      return false;
    }
    return true;
  }

  private onListenOpen(): void {
    console.info('%c[WS] Connected', 'color: #9a6f0f');
  }

  private onListenMessage(event: MessageEvent): void {
    console.info('%c[WS] Message', 'color: #9a6f0f', event.data);

    if (this.isJsonString(event.data)) {
      const message = JSON.parse(event.data);
      this.event.next(message);
    }
  }

  private onListenClose(event: CloseEvent, vmId: string | null): void {
    console.info('%c[WS] Close', 'color: #9a6f0f', event);

    const token = this.authStorageService.getItemStorage('token');

    if (token) {
      if (this.timeout) {
        clearTimeout(this.timeout);
      }

      this.timeout = setTimeout(() => {
        this.init(vmId);
      }, 5000);
    }
  }

  private onListenError(event: Event, vmId: string | null): void {
    console.info('%c[WS] Error', 'color: #ea4c38', event);

    if (this.timeout) {
      clearTimeout(this.timeout);
    }

    this.timeout = setTimeout(() => {
      this.init(vmId);
    }, 5000);
  }

  send(type: string, message: any) {
    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(`${type} ${message}`);
      } else {
        setTimeout(() => {
          this.send(type, message);
        }, 500);
      }
    }
  }

  connect(resource) {
    if (this.ws) {
      if (this.connections[resource]) {
        this.connections[resource]++;
        console.log(`%c[WS] Listener ${resource} subscribed x${this.connections[resource]}`, 'color: #9a6f0f');
      } else {
        this.connections[resource] = 1;
        this.send('add', resource);
      }
    }
  }

  disconnect(resource) {
    if (this.connections[resource]) {
      if (this.connections[resource] > 1) {
        this.connections[resource]--;
        console.log(`%c[WS] Listener ${resource} unsubscribe`, 'color: #9a6f0f');
      } else {
        delete this.connections[resource];
        this.send('delete', resource);
      }
    }
  }

  public close() {
    this.ws.close();
  }
}
