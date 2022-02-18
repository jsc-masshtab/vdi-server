import { AfterViewInit, Component, OnDestroy, OnInit } from '@angular/core';
import { Observable, Subscription } from 'rxjs';

import { EventsService } from '@pages/log/events/all-events/events.service';
import { ICopyrightData, LicenseService } from '@pages/settings/license/license.service';
import { WebsocketService } from '@app/core/services/websock.service';

import * as moment from 'moment-timezone';
import { FooterService } from './footer.service';
import { SystemService } from '@app/pages/settings/system/system.service';
import { map } from 'rxjs/operators';

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
export class FooterComponent implements OnInit, OnDestroy, AfterViewInit {

  public sub: Subscription;
  public socketSub: Subscription;

  public info$: Observable<ICopyrightData>;
  public license: any = {};

  public openedLog: boolean = true;
  public log: string = 'events';

  public countEvents: ICountEvents;

  time = '';
  timezone = '';
  updated_time;

  constructor(
    private licenseService: LicenseService,
    private eventsService: EventsService,
    private systemService: SystemService,
    private ws: WebsocketService
  ) {}

  public ngOnInit(): void {
  
    this.info$ = this.licenseService.getCopyrightInfo();

    this.getLicense();

    this.licenseService.channel$.subscribe(() => {
      this.getLicense();
    });

    this.eventsService.countEvents().valueChanges.subscribe(res => {
      this.countEvents = { ...res.data };
    });

    this.listenSockets();
  }

  ngAfterViewInit() {
    if (this.sub) {
      this.sub.unsubscribe();
    }

    this.sub = this.systemService.getSystemInfo().valueChanges.pipe(map(data => data.data.system_info))
      .subscribe(res => {
      this.updated_time = moment.tz(res.local_time, res.time_zone);
      this.timezone = res.time_zone;

      setInterval(() => {
        this.time = this.updated_time.add(1, 's').format('DD.MM.YYYY HH:mm:ss');
      }, 1000);
      }
    );
  }

  private listenSockets(): void {
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

  public openLog(log: string): void {
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

  public closeLog(): void {
    this.log = '';
    this.openedLog = false;
  }

 
  public getLicense(): void {
    this.licenseService.getLicence().subscribe((res) => {
    
      this.license = res.data;
    });
  }

  public ngOnDestroy(): void {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }
  }
}
