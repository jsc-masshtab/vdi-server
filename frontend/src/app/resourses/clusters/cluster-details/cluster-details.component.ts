import { Component, OnInit } from '@angular/core';
import { ClustersService } from '../all-clusters/clusters.service';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { Router } from '@angular/router';

interface type_cluster {
  [key: string]: any
}


@Component({
  selector: 'vdi-cluster-details',
  templateUrl: './cluster-details.component.html',
  styleUrls: ['./cluster-details.component.scss']
})


export class ClusterDetailsComponent implements OnInit {

  public cluster: type_cluster = {};
  public templates: [] = [];
  public collection: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start'
    },
    {
      title: 'Статус',
      property: 'status'
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
      title: 'Серверы',
      property_array: 'nodes'
    },
    {
      title: 'Пулы данных',
      property_array: 'datapools'
    },
    {
      title: 'Шаблоны ВМ',
      property_array: 'templates'
    },
    {
      title: 'ВМ',
      property_array: 'vms'
    }
  ];
  public collection_nodes = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'server'
    },
    {
      title: 'IP-адрес',
      property: 'management_ip',
      type: 'string'
    },
    {
      title: 'CPU',
      property: 'cpu_count',
      type: 'string'
    },
    {
      title: 'RAM',
      property: 'memory_count',
      type: 'string'
    },
    {
      title: 'Статус',
      property: 'status'
    }
  ];
  public collection_datapools = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'folder-open'
    },
    {
      title: 'Тип',
      property: 'type',
      type: 'string'
    },
    {
      title: 'Диски',
      property: 'vdisk_count',
      type: 'string'
    },
    {
      title: 'Образы',
      property: 'iso_count',
      type: 'string'
    },
    {
      title: 'Файлы',
      property: 'file_count',
      type: 'string'
    },
    {
      title: 'Свободно (Мб)',
      property: 'free_space',
      type: 'string'
    },
    {
      title: 'Занято (Мб)',
      property: 'used_space',
      type: 'string'
    },
    {
      title: 'Статус',
      property: 'status'
    }
  ];
  public collection_templates = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'tv'
    },
    {
      title: 'Cервер',
      property: 'node',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Оперативная память (MБ)',
      property: 'memory_count',
      type: 'string'
    }
  ];
  public collection_vms = [
    {
      title: 'Название',
      property: 'name',
      class: 'name-start',
      type: 'string',
      icon: 'desktop'
    },
    {
      title: 'Сервер',
      property: 'node',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Шаблон',
      property: 'template',
      property_lv2: 'name'
    }
  ];
  public cluster_id: string;
  public menuActive: string = 'info';
  public host: boolean = false;

  constructor(private activatedRoute: ActivatedRoute,
              private service: ClustersService,
              private router: Router) { }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.cluster_id = param.get('id') as string;
      this.getCluster();
    });
  }

  public getCluster() {
    this.host = false;
    this.service.getCluster(this.cluster_id).valueChanges.pipe(map(data => data.data.cluster))
      .subscribe((data) => {
        this.cluster = data;
        this.templates = data.templates.map((item) => JSON.parse(item.info));
        this.host = true;
      },
        () => {
          this.host = true;
        });
  }

  public close() {
    this.router.navigate(['resourses/clusters']);
  }

  public routeTo(route: string): void {
    if (route === 'info') {
      this.menuActive = 'info';
    }

    if (route === 'servers') {
      this.menuActive = 'servers';
    }

    if (route === 'datapools') {
      this.menuActive = 'datapools';
    }

    if (route === 'templates') {
      this.menuActive = 'templates';
    }

    if (route === 'vms') {
      this.menuActive = 'vms';
    }
  }


}
