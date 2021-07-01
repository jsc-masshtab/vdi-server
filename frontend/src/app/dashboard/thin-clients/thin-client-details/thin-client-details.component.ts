import { Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { DisconnectThinClientComponent } from './disconnect-thin-client/disconnect-thin-client.component';
import { ActivatedRoute, ParamMap, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { WebsocketService } from '../../common/classes/websock.service';
import { FormControl } from '@angular/forms';
import { ThinClientsService } from '../thin-clients.service';

import * as moment from 'moment';

@Component({
  selector: 'vdi-thin-client-details',
  templateUrl: './thin-client-details.component.html',
  styleUrls: ['./thin-client-details.component.scss']
})
export class ThinClientDetailsComponent implements OnInit, OnDestroy {

  @ViewChild('messenger', { static: false }) messenger: ElementRef;

  sub: Subscription;
  private socketSub: Subscription;

  id: string;
  entity: any;

  message = new FormControl('')
  messages: any[] = []

  menuActive: string = 'info';

  public collection: object[] = [
    {
      title: 'IP адрес',
      property: 'tk_ip',
      type: 'string'
    },
    {
      title: 'Операционная система',
      property: 'tk_os',
      type: 'string'
    },
    {
      title: 'Версия',
      property: 'veil_connect_version',
      type: 'string'
    },
    {
      title: 'Пользователь',
      property: 'user_name',
      type: 'string'
    },
    {
      title: 'Виртуальная машина',
      property: 'vm_name',
      type: 'string'
    },
    {
      title: 'Время подключения',
      property: 'connected',
      type: 'time'
    },
    {
      title: 'Время отключения',
      property: 'disconnected',
      type: 'time'
    },
    {
      title: 'Время получения данных',
      property: 'data_received',
      type: 'time'
    },
    {
      title: 'Время последней активнасти',
      property: 'last_interaction',
      type: 'time'
    },
    {
      title: 'Статус активности',
      property: 'is_afk',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Не активен', 'Активен']
      }
    },
    {
      title: 'Тип подключения',
      property: 'connection_type',
      type: 'string'
    },
    {
      title: 'Использование TLS',
      property: 'is_connection_secure',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['да', 'нет']
      }
    },
    {
      title: 'Скорость получения данных',
      property: 'read_speed',
      type: 'metric',
      unit: 'байт/сек'
    },
    {
      title: 'Скорость отправки данных',
      property: 'write_speed',
      type: 'metric',
      unit: 'байт/сек'
    },
    {
      title: 'Средний RTT',
      property: 'avg_rtt',
      type: 'metric',
      unit: 'мсек'
    },
    {
      title: 'Процент сетевых потерь',
      property: 'loss_percentage',
      type: 'string'
    }
  ];

  constructor(
    private service: ThinClientsService,
    private activatedRoute: ActivatedRoute,
    private router: Router,
    public dialog: MatDialog,
    private ws: WebsocketService
  ) {

  }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {

      this.id = param.get('id');

      if (history.state.thin_client) {
        this.entity = history.state.thin_client
        this.listenSockets()
        this.messages = []
      } else {
        this.close()
      }
    });
  }


  private listenSockets() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }

    this.socketSub = this.ws.stream('/users/').subscribe((message: any) => {
      if (message.msg_type === 'text_msg' && message.sender_id === this.entity.user_id) {
        this.messages.push({
          sender: message.sender_name,
          self: false,
          text: message.message,
          time: moment().format('HH:mm:ss')
        })

        if (this.messenger) {
          setTimeout(() => {
            this.messenger.nativeElement.scrollTop = this.messenger.nativeElement.scrollHeight
          })
        }
      }
    });
  }

  public routeTo(route: string): void {
    this.menuActive = route;
  }

  public disconnect() {
    this.dialog.open(DisconnectThinClientComponent, {
      disableClose: true,
      width: '500px',
      data: this.entity
    });
  }

  public sendMessage() {

    const message = this.message.value
    this.messages.push({
      sender: 'Вы',
      self: true,
      text: message,
      time: moment().format('HH:mm:ss')
    })

    this.message.setValue('')

    setTimeout(() => {
      this.messenger.nativeElement.scrollTop = this.messenger.nativeElement.scrollHeight
    })
    
    this.service.sendMessageToThinClient(this.entity.user_id, message).subscribe()
  }

  keyEvent(e: KeyboardEvent) {
    if (e.key === 'Enter' && e.ctrlKey) {
      this.sendMessage();
    }
  }

  public close() {
    this.router.navigate(['pages/clients/session/']);
  }

  ngOnDestroy() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }
  }
}
