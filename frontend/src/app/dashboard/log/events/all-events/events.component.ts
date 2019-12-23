import { EventsService } from './events.service';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { Component, OnInit } from '@angular/core';
import { map } from 'rxjs/operators';

@Component({
  selector: 'vdi-events',
  templateUrl: './events.component.html',
  styleUrls: ['./events.component.scss']
})

export class EventsComponent  implements OnInit {

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

  constructor(private service: EventsService, private waitService: WaitService) {
  }

  ngOnInit() {
    this.getEvents();
  }

  public getEvents() {
    this.waitService.setWait(true);
    this.service.getAllEvents().valueChanges.pipe(map(data => data.data.events))
      .subscribe((data) => {
        this.events = data;
        this.waitService.setWait(false);
      });
  }

}
