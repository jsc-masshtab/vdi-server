import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';

interface Event {
  event: {
    created: string
    event_type: number
    message: string
    user: string
  }
}

interface IData {
  event: Event
}

@Component({
  selector: 'vdi-info-event',
  templateUrl: './info-event.component.html',
  styleUrls: ['./info-event.component.scss']
})
export class InfoEventComponent implements OnInit {

  event: Event

  public collection: any[] = [
    {
      title: 'Событие',
      property: 'message',
      type: 'string'
    },
    {
      title: 'Пользователь',
      property: 'user',
      type: 'string'
    },
    {
      title: 'Создан',
      property: 'created',
      type: 'string'
    }
  ];

  constructor(@Inject(MAT_DIALOG_DATA) public data: IData) {
    this.event = {...data.event}
  }

  ngOnInit() {
  }

}