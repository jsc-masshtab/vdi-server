import { Component, OnInit } from '@angular/core';
import { ClustersService } from '../clusters.service';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap, Router } from '@angular/router';

@Component({
  selector: 'vdi-cluster-details',
  templateUrl: './cluster-details.component.html',
  styleUrls: ['./cluster-details.component.scss']
})


export class ClusterDetailsComponent implements OnInit {

  public cluster: {} = {};
  public templates: [] = [];
  public collection = [
    {
      title: 'Название',
      property: 'verbose_name'
    },
    {
      title: 'Серверы',
      property: "nodes_count"
     
    },
    {
      title: 'CPU',
      property: 'cpu_count'
    },
    {
      title: 'RAM',
      property: 'memory_count'
    },
    {
      title: 'Статус',
      property: 'status'
    }
  ];
  public collection_nodes = [
    {
      title: 'Название',
      property: 'verbose_name'
    },
    {
      title: 'Локация',
      property: "datacenter_name"
    },
    {
      title: 'IP-адрес',
      property: 'management_ip'
    },
    {
      title: 'CPU',
      property: 'cpu_count'
    },
    {
      title: 'RAM',
      property: 'memory_count'
    },
    {
      title: 'Статус',
      property: 'status'
    }
  ];
  public collection_datapools = [
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
  public collection_templates = [
    {
      title: 'Название',
      property: 'verbose_name'
    },
    {
      title: 'Cервер',
      property: "node",
      property_lv2: 'verbose_name'
    },
    {
      title: 'Операционная система',
      property: 'os_type'
    },
    {
      title: 'Оперативная память (MБ)',
      property: 'memory_count'
    },
    {
      title: 'Графический адаптер',
      property: 'video',
      property_lv2: 'type'
    },
    {
      title: 'Звуковой адаптер',
      property: 'sound',
      property_lv2: 'model',
      property_lv2_prop2: 'codec'
    },
    {
      title: 'Высокая доступность',
      property_boolean: 'ha_enabled',
      property_boolean_true: 'Включена',
      property_boolean_false: 'Выключена'
    }
  ];
  public collection_vms = [
    {
      title: 'Название',
      property: 'name'
    },
    {
      title: 'Сервер',
      property: "node",
      property_lv2: 'verbose_name'
    },
    {
      title: 'Шаблон',
      property: "template",
      property_lv2: 'name'
    }
  ];
  public cluster_id:string;
  public menuActive:string = 'info';
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

  public spinner:boolean = false;

  constructor(private activatedRoute: ActivatedRoute,
              private router: Router,
              private service: ClustersService){}

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.cluster_id = param.get('id') as string;
      this.getCluster(this.cluster_id);
    });
  }

  private getCluster(id:string) {
    this.spinner = true;
    this.service.getCluster(id).valueChanges.pipe(map(data => data.data.cluster))
      .subscribe( (data) => {
        this.cluster = data;
     
        this.templates = data.templates.map((item) => JSON.parse(item.info));
        this.crumbs.push({
            title: `Кластер ${this.cluster['verbose_name']}`,
            icon: 'building'
          }
        );
      
        this.spinner = false;
      },
      (error)=> {
        this.spinner = false;
      });
  }

  public routeTo(route:string): void {
    if(route === 'info') {
      this.menuActive = 'info';
    }

    if(route === 'servers') {
      this.menuActive = 'servers';
    }

    if(route === 'datapools') {
      this.menuActive = 'datapools';
    }

    if(route === 'templates') {
      this.menuActive = 'templates';
    }

    if(route === 'vms') {
      this.menuActive = 'vms';
    }
  }


}
