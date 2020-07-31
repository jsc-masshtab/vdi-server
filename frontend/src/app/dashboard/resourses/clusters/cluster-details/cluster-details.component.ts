import { Component, OnInit, OnDestroy } from '@angular/core';
import { ClustersService } from '../all-clusters/clusters.service';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

interface ICollection {
  [index: string]: string;
}


@Component({
  selector: 'vdi-cluster-details',
  templateUrl: './cluster-details.component.html',
  styleUrls: ['./cluster-details.component.scss']
})


export class ClusterDetailsComponent implements OnInit, OnDestroy {

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
    }/* ,
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
    } */
  ];
  public collectionNodes = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'server'
    },
    /* {
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
    }, */
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
    }
  ];
  public collectionVms = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'desktop'
    },
    {
      title: 'Шаблон',
      property: 'template',
      property_lv2: 'verbose_name'
    }
  ];
  public idCluster: string;
  public menuActive: string = 'info';
  public host: boolean = false;
  private address: string;

  private sub: Subscription;

  constructor(private activatedRoute: ActivatedRoute,
              private service: ClustersService,
              private router: Router) { }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.idCluster = param.get('id');
      this.address = param.get('address');
      this.getCluster();
    });
  }

  public getCluster() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
    this.host = false;
    this.sub = this.service.getCluster(this.idCluster, this.address).valueChanges.pipe(map(data => data.data.cluster))
      .subscribe((data) => {
        this.cluster = data;
        this.host = true;
      },
        () => {
          this.host = true;
        });
  }

  public close() {
    this.router.navigate(['pages/resourses/clusters']);
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

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }


}
