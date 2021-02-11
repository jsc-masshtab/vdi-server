import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { DetailsMove } from '../common/classes/details-move';
import { Subscription } from 'rxjs';
import { FormControl } from '@angular/forms';
import { ThinClientsService } from './thin-clients.service';
import { MatDialog } from '@angular/material';
import { WaitService } from '../common/components/single/wait/wait.service';
import { Router } from '@angular/router';
import { map } from 'rxjs/operators';
import { IParams } from 'types';

@Component({
  selector: 'vdi-thin-clients',
  templateUrl: './thin-clients.component.html',
  styleUrls: ['./thin-clients.component.scss']
})
export class ThinClientsComponent extends DetailsMove implements OnInit {

  private getThinClientSub: Subscription;

  public limit = 100;
  public count = 0;
  public offset = 0;

  user = new FormControl('');

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
    private router: Router
  ) { 
    super();
  }

  @ViewChild('view') view: ElementRef;

  ngOnInit() {
    this.refresh();

    this.user.valueChanges.subscribe(() => {
      this.getAll();
    });

  }

  public refresh(): void {
    this.service.params.spin = true;
    this.getAll();
  }


  public getAll() {
    if (this.getThinClientSub) {
      this.getThinClientSub.unsubscribe();
    }

    const queryset = {
      user_id: this.user.value
    };

    if (this.user.value == '') {
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
  }
}