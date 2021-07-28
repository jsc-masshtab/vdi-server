import { Component, OnInit, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { Router } from '@angular/router';
import { IParams } from '@shared/types';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';

import { WaitService } from '../../core/components/wait/wait.service';
import { DetailsMove } from '../../shared/classes/details-move';
import { WebsocketService } from '../../shared/classes/websock.service';
import { ThinClientsService } from './thin-clients.service';

@Component({
  selector: 'vdi-thin-clients',
  templateUrl: './thin-clients.component.html',
  styleUrls: ['./thin-clients.component.scss']
})
export class ThinClientsComponent extends DetailsMove implements OnInit, OnDestroy {

  private socketSub: Subscription;
  private getThinClientSub: Subscription;

  public limit = 100;
  public count = 0;
  public offset = 0;

  user = new FormControl('');
  disconnected = new FormControl(false)

  public data: [];

  public collection: object[] = [
    {
      title: 'IP адрес',
      property: 'tk_ip',
      class: 'name-start',
      icon: 'laptop',
      type: 'string',
      sort: true
    },
    {
      title: 'Операционная система',
      property: 'tk_os',
      type: 'string',
      sort: true
    },
    {
      title: 'Версия',
      property: 'veil_connect_version',
      type: 'string',
      sort: true
    },
    {
      title: 'Пользователь',
      property: 'user_name',
      type: 'string',
      sort: true
    },
    {
      title: 'Виртуальная машина',
      property: 'vm_name',
      type: 'string',
      sort: true
    },
    {
      title: 'Время подключения',
      property: 'connected',
      type: 'time',
      class: 'name-end',
      sort: true
    }
  ];

  constructor(
    private service: ThinClientsService,
    public dialog: MatDialog,
    private waitService: WaitService,
    private router: Router,
    private ws: WebsocketService
  ) { 
    super();
  }

  @ViewChild('view', { static: true }) view: ElementRef;

  ngOnInit() {
    this.refresh();
    this.listenSockets();

    this.user.valueChanges.subscribe(() => {
      this.getAll();
    });


    this.disconnected.valueChanges.subscribe(() => {
      this.getAll();
    });
  }

  public refresh(): void {
    this.service.params.spin = true;
    this.getAll();
  }

  private listenSockets() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }

    this.socketSub = this.ws.stream('/thin_clients/').subscribe((message: any) => {
      if (message['msg_type'] === 'data') {
        this.refresh();
      }
    });
  }

  public getAll() {
    if (this.getThinClientSub) {
      this.getThinClientSub.unsubscribe();
    }

    const queryset = {
      user_id: this.user.value,
      get_disconnected: this.disconnected.value
    };

    if (this.user.value === '') {
      delete queryset['user_id'];
    }

    this.waitService.setWait(true);

    this.service.getThinClients(queryset).valueChanges.pipe(map(data => data.data))
      .subscribe((data) => {
        this.data = data.thin_clients;
        this.count = data.thin_clients_count;
        this.waitService.setWait(false);
      });
  }

  public sortList(param: IParams): void {
    this.service.params.spin = param.spin;
    this.service.params.nameSort = param.nameSort;
    this.getAll();
  }

  public toPage(message: any): void {
    this.offset = message.offset;
    this.getAll();
  }

  public routeTo(item): void {
    this.router.navigate([`pages/clients/session/${item.conn_id}`], { state: { thin_client: item }});
  }

  public onResize(): void {
    super.onResize(this.view);
  }

  public componentActivate(): void {
    super.componentActivate(this.view);
  }

  public componentDeactivate(): void {
    super.componentDeactivate();
  }

  ngOnDestroy() {
    this.service.params.spin = true;
    this.service.params.nameSort = undefined;

    if (this.getThinClientSub) {
      this.getThinClientSub.unsubscribe();
    }

    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }
  }
}
