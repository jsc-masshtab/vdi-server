import { Component, OnInit } from '@angular/core';
import { ClustersService } from './clusters.service';
import { map } from 'rxjs/operators';

@Component({
  selector: 'vdi-clusters',
  templateUrl: './clusters.component.html',
  styleUrls: ['./clusters.component.scss']
})


export class ClustersComponent implements OnInit {

  public infoTemplates: [];
  public collection: object[] = [];
  public crumbs: object[] = [
    {
      title: 'Серверы',
      icon: 'server'
    },
    {
      title: 'Кластеры',
      icon: 'server'
    }
  ];

  public spinner:boolean = true;

  constructor(private service: ClustersService){}

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
        title: 'Названиеrrr',
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
