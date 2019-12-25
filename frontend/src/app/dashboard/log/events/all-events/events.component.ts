import { EventsService } from './events.service';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { Component, OnInit } from '@angular/core';
import { map } from 'rxjs/operators';
import { MatDialog } from '@angular/material';
import { InfoEventComponent } from '../info-event/info-event.component';

@Component({
  selector: 'vdi-events',
  templateUrl: './events.component.html',
  styleUrls: ['./events.component.scss']
})

export class EventsComponent implements OnInit {
  
  public limit = 100;
  public count = 0;
  public offset = 0;

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
      class: 'name-end'
    },
    {
      title: 'Дата создания',
      property: 'created',
      type: 'time',
      class: 'name-end'
    }
  ];

  public events: object[] = [];

  constructor(
    private service: EventsService,
    private waitService: WaitService,
    public dialog: MatDialog) { }
  
  ngOnInit() {
    this.refresh();
  }

  public refresh(): void {
    this.getEvents();
  }

  public execute(e) {
    const event = { ...e }
    this.openEventDetails(event)
  }

  public getEvents() {
    this.waitService.setWait(true);
    this.service.getAllEvents().valueChanges.pipe(map(data => data.data.events))
      .subscribe((data) => {
        this.events = data;
        this.count = this.events.length;
        this.waitService.setWait(false);
      });
  }

  public openEventDetails(event): void {
    this.dialog.open(InfoEventComponent, {
      width: '700px',
      data: {
        event: event
      }
    });
  }
}
