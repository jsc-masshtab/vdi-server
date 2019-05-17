import { Component, OnInit } from '@angular/core';
import { DatapoolsService } from './datapools.service';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap, Router } from '@angular/router';

@Component({
  selector: 'vdi-datapools',
  templateUrl: './datapools.component.html',
  styleUrls: ['./datapools.component.scss']
})


export class DatapoolsComponent implements OnInit {

  public infoTemplates: [];
  public collection: object[] = [];
  public datapools: {};
  private id_node:string;
  private id_cluster:string;

  public crumbs: object[] = [
    {
      title: 'Ресурсы',
      icon: 'database'
    },
    {
      title: 'Кластеры',
      icon: 'building',
      route: 'resourses/clusters'
    }
  ];

  public spinner:boolean = true;

  constructor(private service: DatapoolsService,private activatedRoute: ActivatedRoute,private router: Router){}

  ngOnInit() {
    this.collectionAction();
    console.log(this.router);
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.id_node = param.get('id') as string;
      this.getDatapools(this.id_node);
    });
  }

  private getDatapools(id_node) {
    this.service.getAllDatapools(id_node).valueChanges.pipe(map(data => data.data.datapools))
      .subscribe( (data) => {
        this.datapools = data;

        console.log(this.datapools,'datapools');

        let cluster_name = localStorage.getItem('cluster_name');
        let node_name = localStorage.getItem('node_name');
        let node_id = localStorage.getItem('node_id');
        let cluster_id = localStorage.getItem('cluster_id');

        this.crumbs = [
          {
            title: 'Ресурсы',
            icon: 'database'
          },
          {
            title: `Кластер ${cluster_name}`,
            icon: 'building',
            route: `resourses/clusters/`
          },
          {
            title: `Сервер ${node_name}`,
            icon: 'building',
            route: `resourses/clusters/${cluster_id}/nodes/`
          },
          {
            title: `Пулы`,
            icon: 'building',
            route: `resourses/clusters/${cluster_id}/nodes/${node_id}/datapools`
          }
      ]


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
        title: 'Тип',
        property: "type"
      },
      {
        title: 'Диски',
        property: 'vdisk_count'
      },
      {
        title: 'Образы',
        property: 'iso_count'
      },
      {
        title: 'Файлы',
        property: 'file_count'
      },
      {
        title: 'Свободно (Мб)',
        property: 'free_space'
      },
      {
        title: 'Занято (Мб)',
        property: 'used_space'
      },
      {
        title: 'Статус',
        property: 'status'
      }
    ];
  }
}
