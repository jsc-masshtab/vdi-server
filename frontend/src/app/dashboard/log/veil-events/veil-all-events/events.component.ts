import { VeilEventsService } from './events.service';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { map } from 'rxjs/operators';
import { MatDialog } from '@angular/material/dialog';
import { VeilInfoEventComponent } from '../veil-info-event/info-event.component';
import { FormControl } from '@angular/forms';
import { IParams } from 'types';
import { Subscription } from 'rxjs';
import { WebsocketService } from 'src/app/dashboard/common/classes/websock.service';

interface Event {
  event: {
    created: string
    event_type: number
    message: string
    user: string
  };
}

@Component({
  selector: 'vdi-events',
  templateUrl: './events.component.html',
  styleUrls: ['./events.component.scss']
})

export class VeilEventsComponent implements OnInit, OnDestroy {

  private socketSub: Subscription;

  public limit = 100;
  public count = 0;
  public offset = 0;

  event_type = new FormControl('all');
  controller = new FormControl('all');

  controllers = [];

  public collection: object[] = [
    {
      title: 'Сообщение',
      property: 'message',
      class: 'name-start',
      type: 'string',
      icon: 'comment'
    },
    {
      title: 'Cоздатель',
      property: 'user',
      type: 'string',
      class: 'name-end',
      sort: true
    },
    {
      title: 'Дата создания',
      property: 'created',
      type: 'time',
      class: 'name-end',
      sort: true
    }
  ];

  public events: object[] = [];

  public queryset: any;

  constructor(
    private service: VeilEventsService,
    private waitService: WaitService,
    public dialog: MatDialog,
    private ws: WebsocketService
  ) { }

  ngOnInit() {
    this.refresh();
    this.listenSockets();

    this.event_type.valueChanges.subscribe(() => {
      this.getEvents();
    });


    this.controller.valueChanges.subscribe(() => {
      this.getEvents();
    });

  }

  public refresh(): void {
    this.getEvents();
    this.getAllControllers();
  }

  public clickRow(event): void {
    this.openEventDetails(event);
  }

  public toPage(message: any): void {
    this.offset = message.offset;
    this.getEvents();
  }

  public sortList(param: IParams): void {
    this.service.paramsForGetEvents.spin = param.spin;
    this.service.paramsForGetEvents.nameSort = param.nameSort;
    this.getEvents();
  }

  public getAllControllers() {
    this.service.getAllControllers().valueChanges.pipe(map(data => data.data))
      .subscribe((data) => {
        this.controllers = data.controllers
      });
  }

  public getEvents(): void {


    const queryset = {
      offset: this.offset,
      limit: this.limit,
      controller: this.controller.value,
      event_type: this.event_type.value
    };


    if (this.event_type.value === 'all') {
      delete queryset['event_type'];
    }

    if (this.controller.value === 'all') {
      delete queryset['controller'];
    }

    this.queryset = queryset;

    this.waitService.setWait(true);
    this.service.getAllEvents(queryset).valueChanges.pipe(map(data => data.data))
      .subscribe((data) => {
        this.events = [...data.veil_events];
        this.count = data.veil_events_count;
        this.waitService.setWait(false);
      });
  }

  private listenSockets() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }

    this.socketSub = this.ws.stream('/events/').subscribe(() => {
      this.service.getAllEvents(this.queryset).refetch();
    });
  }

  public openEventDetails(event: Event): void {
    this.dialog.open(VeilInfoEventComponent, {
      disableClose: true,
      width: '700px',
      data: {
        event
      }
    });
  }

  ngOnDestroy() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }
  }
}
