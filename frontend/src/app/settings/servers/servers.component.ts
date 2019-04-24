import { Component, OnInit } from '@angular/core';
import { ServersService   } from './servers.service';
import { map } from 'rxjs/operators';

@Component({
  selector: 'vdi-servers',
  templateUrl: './servers.component.html',
  styleUrls: ['./servers.component.scss']
})


export class ServersComponent implements OnInit {

  public infoTemplates: [];
  public collection: object[] = [];
  public crumbs: object[] = [
    {
      title: 'Настройки',
      icon: 'cog'
    },
    {
      title: 'Серверы',
      icon: 'server',
      route: 'settings/servers'
    }
  ];

  public spinner:boolean = true;


  constructor(private service: ServersService){}

  ngOnInit() {
    this.collectionAction();
    this.getAllTeplates();
  }

  private getAllTeplates() {
    this.service.getAllTeplates().valueChanges.pipe(map(data => data.data.templates))
      .subscribe( (data) => {
        this.infoTemplates = data.map((item) => JSON.parse(item.info));
        this.spinner = false;
      },
      (error)=> {
        this.spinner = false;
      });
  }

  public collectionAction(): void {
    this.collection = [
      {
        title: 'Название',
        property: 'verbose_name'
      },
      {
        title: 'IP-адрес',
        property: "node",
        property_lv2: 'verbose_name'
      },
      {
        title: 'CPU',
        property: 'os_type'
      },
      {
        title: 'RAM',
        property: 'memory_count'
      },
      {
        title: 'ВМ',
        property: 'video',
        property_lv2: 'type'
      },
      {
        title: 'Статус',
        property: 'sound',
        property_lv2: 'model',
        property_lv2_prop2: 'codec'
      }
    ];
  }

}
