import { Component, OnInit, OnDestroy, Input } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';

import { WaitService } from '@core/components/wait/wait.service';

import { WebsocketService } from '@shared/classes/websock.service';
import { IParams } from '@shared/types';

import { AddExportComponent } from '../add-exports/add-exports.component';
import { InfoEventComponent } from '../info-event/info-event.component';
import { EventsService } from './events.service';

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

export class EventsComponent implements OnInit, OnDestroy {

  @Input() controls: boolean = true;
  @Input() set type(value) {
    this.event_type.setValue(value);
  }

  private socketSub: Subscription;

  public limit = 100;
  public count = 0;
  public offset = 0;

  start_date = new FormControl(0);
  end_date = new FormControl(new Date());
  event_type = new FormControl('all');
  entity_type = new FormControl('all');
  user = new FormControl('all');
  readed = new FormControl(false);

  users = [];
  entity_types = [];
  selected_user: string = '';

  public collection: object[] = [
    {
      title: 'Сообщение',
      property: 'message',
      class: 'name-start',
      type: 'string',
      icon: 'comment'
    },
    {
      title: 'Создатель',
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
    private service: EventsService,
    private waitService: WaitService,
    public dialog: MatDialog,
    private ws: WebsocketService
  ) { }

  ngOnInit() {
    this.refresh();
    this.listenSockets();

    this.start_date.valueChanges.subscribe(() => {
      this.getEvents();
    });

    this.end_date.valueChanges.subscribe(() => {
      this.getEvents();
    });

    this.event_type.valueChanges.subscribe(() => {
      this.getEvents();
    });

    this.entity_type.valueChanges.subscribe(() => {
      this.getEvents();
    });

    this.user.valueChanges.subscribe((user) => {

      const id = this.users.findIndex(found => found.username ? found.username === user : false);

      if (id !== -1) {
        this.selected_user = this.users[id].id;
      } else {
        this.selected_user = '';
      }

      this.getEvents();
    });

    this.readed.valueChanges.subscribe(() => {
      this.getEvents();
    });
  }

  public refresh(): void {
    this.getEvents();
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

  public getEvents(): void {

    const start_date = new Date(this.start_date.value).setHours(0, 0, 0);
    const end_date = new Date(this.end_date.value).setHours(23, 59, 59);

    const queryset = {
      offset: this.offset,
      limit: this.limit,
      start_date: new Date(start_date).toISOString(),
      end_date: new Date(end_date).toISOString(),
      event_type: this.event_type.value,
      entity_type: this.entity_type.value,
      user: this.user.value
    };

    if (this.readed.value && this.selected_user) {
      queryset['read_by'] = this.selected_user;
    }

    if (this.user.value === 'all') {
      delete queryset['user'];
    }

    if (this.event_type.value === 'all') {
      delete queryset['event_type'];
    }

    if (this.entity_type.value === 'all') {
      delete queryset['entity_type'];
    }

    this.queryset = queryset;

    this.waitService.setWait(true);
    this.service.getAllEvents(queryset).valueChanges.pipe(map(data => data.data))
      .subscribe((data) => {
        this.events = [...data.events];
        this.entity_types = [...data.entity_types];
        this.count = data.count;
        this.waitService.setWait(false);
        this.users = [...data.users];
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
    this.dialog.open(InfoEventComponent, {
      disableClose: true,
      width: '700px',
      data: {
        event
      }
    });
  }

  public openExports(): void {
    this.dialog.open(AddExportComponent, {
      disableClose: true,
      width: '700px',
      data: {
        queryset: this.queryset
      }
    });
  }

  ngOnDestroy() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }
  }
}
