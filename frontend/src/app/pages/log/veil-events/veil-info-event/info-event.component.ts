import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';

interface Event {
  event: {
    created: string
    event_type: number
    message: string
    user: string
  };
}

interface IData {
  event: Event;
}

@Component({
  selector: 'vdi-info-event',
  templateUrl: './info-event.component.html',
  styleUrls: ['./info-event.component.scss']
})
export class VeilInfoEventComponent {

  event: Event;

  public collection: any[] = [
    {
      title: 'Событие',
      property: 'message',
      type: 'string'
    },
    {
      title: 'Описание',
      property: 'description',
      type: 'string'
    },
    {
      title: 'Пользователь',
      property: 'user',
      type: 'string'
    },
    {
      title: 'Дата создания',
      property: 'created',
      type: 'time'
    }
  ];

  constructor(@Inject(MAT_DIALOG_DATA) public data: IData) {
    this.event = data.event;
  }
}
