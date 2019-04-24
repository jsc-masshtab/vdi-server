import { Component, OnInit } from '@angular/core';
import { NodesService } from './nodes.service';
import { map } from 'rxjs/operators';

@Component({
  selector: 'vdi-nodes',
  templateUrl: './nodes.component.html',
  styleUrls: ['./nodes.component.scss']
})


export class NodesComponent implements OnInit {

  public infoTemplates: [];
  public collection: object[] = [];
  //private nodeId: string;
  public crumbs: object[] = [
    {
      title: 'Ресурсы',
      icon: 'server'
    },
    {
      title: 'Кластеры',
      icon: 'server',
      route: 'resourses/clusters'
    },
    {
      title: 'Серверы',
      icon: 'server',
      route: 'resourses/clusters/:id/servers'
    }
  ];

  public spinner:boolean = true;


  constructor(private service: NodesService){}

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

  // public clickNode(event): void {
  //   this.nodeId = event.id;
  //   this.router.navigate([`page/nodes/${this.nodeId}/clusters`]);
  // }




}
