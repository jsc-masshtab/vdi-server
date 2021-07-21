import { Component, OnDestroy, OnInit } from '@angular/core';
import { FooterService } from './footer.service';

import { Subscription } from 'rxjs';
import { WebsocketService } from '../../../common/classes/websock.service';

interface ICountEvents {
  warning: number;
  error: number;
  all: number;
}

@Component({
  selector: 'vdi-footer',
  templateUrl: './footer.component.html',
  styleUrls: ['./footer.component.scss']
})
export class FooterComponent implements OnInit, OnDestroy {

  socketSub: Subscription;

  info: any = {};
  license: any = {};

  openedLog: boolean = true;
  log: string = 'events';

  countEvents: ICountEvents;

  constructor(
    private service: FooterService,
    private ws: WebsocketService
  ) {}

  ngOnInit() {
    this.service.getInfo().subscribe((res) => {
      this.info = res.data;
    });

    this.getLicense();

    this.service.channel$.subscribe(() => {
      this.getLicense();
    });

    this.service.countEvents().valueChanges.subscribe(res => {
      this.countEvents = { ...res.data };
    });

    this.listenSockets();
  }

  private listenSockets() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }

    this.socketSub = this.ws.stream('/events/').subscribe((message: any) => {
      if (message.msg_type === 'data') {
        if (message.event_type === 1) { this.countEvents.warning++ }
        if (message.event_type === 2) { this.countEvents.error++ }
        this.countEvents.all++;
      }
    });
  }

  openLog(log) {
    if (log !== this.log) {
      this.openedLog = false;
      this.log = log;

      setTimeout(() => {
        this.openedLog = true;
      })
    } else {
      this.closeLog();
    }
  }

  closeLog() {
    this.log = '';
    this.openedLog = false;
  }

 
  getLicense() {
    this.service.getLicence().subscribe((res) => {
      this.license = res.data;
    });
  }

  ngOnDestroy() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }
  }
}
