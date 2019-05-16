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
  private route_info: string;

  public crumbs: object[] = [
    {
      title: 'Ресурсы',
      icon: 'database'
    }
  ];

  public spinner:boolean = true;

  constructor(private service: DatapoolsService,private activatedRoute: ActivatedRoute,private router: Router){}

  ngOnInit() {
    this.collectionAction();
 
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {              // объединить потоки
      this.id_node = param.get('id') as string;
      this.getDatapools(this.id_node);
    });

    this.activatedRoute.data.subscribe((data: string) => {
      this.route_info = data['route_info'];
    });
  }

  private getDatapools(id_node) {
    this.service.getAllDatapools(id_node).valueChanges.pipe(map(data => data.data.datapools))
      .subscribe( (data) => {
        this.datapools = data;

        let cluster_name = localStorage.getItem('cluster_name');
        let node_name = localStorage.getItem('node_name');
        let node_id = localStorage.getItem('node_id');
        let cluster_id = localStorage.getItem('cluster_id');

        if(this.id_node) {    
          if(this.route_info === 'nodes-datapools')   {
            this.crumbs.push(  // переход из общей вкладки серверы
              {
                title: `Сервер ${node_name}`,
                icon: 'server',
                route: `resourses/nodes/`
              },
              {
                title: `Пулы`,
                icon: 'folder-open'
              }
            )
          } else {
            this.crumbs.push(  // переход из рес-сы - имя класт - имя серв - пул
              {
                title: `Кластер ${cluster_name}`,
                icon: 'building',
                route: `resourses/clusters/`
              },
              {
                title: `Сервер ${node_name}`,
                icon: 'server',
                route: `resourses/clusters/${cluster_id}/nodes/`
              },
              {
                title: `Пулы`,
                icon: 'folder-open'
              }
            )
          }    
        } else {        // из общей пулы
          this.crumbs.push(
            {
              title: `Пулы`,
              icon: 'folder-open'
            }
          );
        }
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
