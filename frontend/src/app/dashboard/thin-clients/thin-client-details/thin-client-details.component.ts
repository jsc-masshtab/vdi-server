import { Component, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material';
import { DisconnectThinClientComponent } from './disconnect-thin-client/disconnect-thin-client.component';
import { ActivatedRoute, ParamMap, Router } from '@angular/router';
import { Subscription } from 'rxjs';

@Component({
  selector: 'vdi-thin-client-details',
  templateUrl: './thin-client-details.component.html',
  styleUrls: ['./thin-client-details.component.scss']
})
export class ThinClientDetailsComponent implements OnInit {

  sub: Subscription;

  id: string;
  entity: any;

  menuActive: string = 'info';
  
  public collection: object[] = [
    {
      title: 'Ip адрес',
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
      title: 'Время получения',
      property: 'data_received',
      type: 'time'
    },
    {
      title: 'Время взаимодействия',
      property: 'last_interaction',
      type: 'time'
    },
    {
      title: 'Статус активности',
      property: 'is_afk',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['В ожидании', 'Активный']
      }
    }
  ];

  constructor(
    private activatedRoute: ActivatedRoute,
    private router: Router,
    public dialog: MatDialog
  ) { 
    
  }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      
      this.id = param.get('id');

      if (history.state.thin_client) {
        this.entity = history.state.thin_client
      } else {
        this.close()
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

  public close() {
    this.router.navigate([`pages/clients/session/`]);
  }
}
