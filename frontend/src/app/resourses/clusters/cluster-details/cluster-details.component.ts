import { Component, OnInit } from '@angular/core';
import { ClustersService } from '../all-clusters/clusters.service';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { Router } from '@angular/router';

interface ICollection {
  [index: string]: string;
}


@Component({
  selector: 'vdi-cluster-details',
  templateUrl: './cluster-details.component.html',
  styleUrls: ['./cluster-details.component.scss']
})


export class ClusterDetailsComponent implements OnInit {

  public cluster: ICollection = {};
  public templates: [] = [];
  public collectionDetails: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string'
    },
    {
      title: 'Статус',
      property: 'status'
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
      title: 'Серверы',
      property: 'nodes',
      type: 'array-length'
    },
    {
      title: 'Пулы данных',
      property: 'datapools',
      type: 'array-length'
    },
    {
      title: 'Шаблоны ВМ',
      property: 'templates',
      type: 'array-length'
    },
    {
      title: 'ВМ',
      property: 'vms',
      type: 'array-length'
    }
  ];
  public collectionNodes = [
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
  public collectionDatapools = [
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
  public collectionTemplates = [
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
  public collectionVms = [
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
  public idCluster: string;
  public menuActive: string = 'info';
  public host: boolean = false;

  constructor(private activatedRoute: ActivatedRoute,
              private service: ClustersService,
              private router: Router) { }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.idCluster = param.get('id') as string;
      this.getCluster();
    });
  }

  public getCluster() {
    this.host = false;
    this.service.getCluster(this.idCluster).valueChanges.pipe(map(data => data.data.cluster))
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
