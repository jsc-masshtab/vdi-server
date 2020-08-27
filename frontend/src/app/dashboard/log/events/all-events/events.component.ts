import { EventsService } from './events.service';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { Component, OnInit } from '@angular/core';
import { map } from 'rxjs/operators';
import { MatDialog } from '@angular/material';
import { InfoEventComponent } from '../info-event/info-event.component';
import { FormControl } from '@angular/forms';
import { IParams } from 'types';

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

export class EventsComponent implements OnInit {

  public limit = 100;
  public count = 0;
  public offset = 0;

  start_date = new FormControl(new Date());
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

  constructor(
    private service: EventsService,
    private waitService: WaitService,
    public dialog: MatDialog) { }
  ngOnInit() {
    this.refresh();

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
    this.getAllUsers();
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

  public getAllUsers(): void {
    this.service.getAllUsers().valueChanges.pipe(map(data => data.data))
      .subscribe((data) => {
        this.users = [...data.users];
      });
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

    this.waitService.setWait(true);
    this.service.getAllEvents(queryset).valueChanges.pipe(map(data => data.data))
      .subscribe((data) => {
        this.events = [...data.events];
        this.entity_types = [...data.entity_types];
        this.count = data.count;
        this.waitService.setWait(false);
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
}
