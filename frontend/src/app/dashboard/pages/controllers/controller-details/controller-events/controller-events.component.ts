import { Component, OnDestroy, OnInit, Input } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';
import { WaitService } from 'src/app/dashboard/core/components/wait/wait.service';
import { ControllerEventsService } from './controller-events.service';
import { InfoEventComponent } from 'src/app/dashboard/pages/log/events/info-event/info-event.component'


@Component({
  selector: 'vdi-controller-events',
  templateUrl: './controller-events.component.html',
  styleUrls: ['./controller-events.component.scss']
})
export class ControllerEventsComponent implements OnInit, OnDestroy {

  @Input() controller: any

  private socketSub: Subscription;

  public limit = 100;
  public count = 0;
  public offset = 0;

  event_type = new FormControl('all');

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
    private service: ControllerEventsService,
    private waitService: WaitService,
    public dialog: MatDialog
  ) { }

  ngOnInit() {
    this.refresh();
    this.listenSockets();

    this.event_type.valueChanges.subscribe(() => {
      this.getEvents();
    });
  }

  public refresh(): void {
    this.getEvents();
  }

  public toPage(message: any): void {
    this.offset = message.offset;
    this.getEvents();
  }

  public sortList(param: any): void {
    this.service.paramsForGetEvents.spin = param.spin;
    this.service.paramsForGetEvents.nameSort = param.nameSort;
    this.getEvents();
  }

  public getEvents(): void {

    const queryset = {
      offset: this.offset,
      limit: this.limit,
      event_type: this.event_type.value,
      controller: this.controller.id
    };

    if (this.event_type.value === 'all') {
      delete queryset['event_type'];
    }

    this.queryset = queryset;

    this.waitService.setWait(true);

    this.service.getAllEvents(queryset).valueChanges.pipe(map(data => data.data.controller))
      .subscribe((data) => {
        this.events = [...data.veil_events];
        this.count = data.veil_events_count;
        this.waitService.setWait(false);
      });
  }

  public clickRow(event): void {
    this.openEventDetails(event);
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

  private listenSockets() {
   /*  if (this.socketSub) {
      this.socketSub.unsubscribe();
    }

    this.socketSub = this.ws.stream('/events/').subscribe(() => {
      this.service.getAllEvents(this.queryset).refetch();
    }); */
  }

  ngOnDestroy() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }
  }
}
