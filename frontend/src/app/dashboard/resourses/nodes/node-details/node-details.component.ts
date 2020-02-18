
import { Component, OnInit, OnDestroy } from '@angular/core';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { Router } from '@angular/router';
import { NodesService } from '../all-nodes/nodes.service';
import { Subscription } from 'rxjs';

interface type_node {
  [key: string]: any
}


@Component({
  selector: 'vdi-node-details',
  templateUrl: './node-details.component.html',
  styleUrls: ['./node-details.component.scss']
})


export class NodeDetailsComponent implements OnInit, OnDestroy {

  public node: type_node = {};
  public templates: [] = [];
  public collection = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string'
    },
    {
      title: 'Кластер',
      property: 'cluster',
      property_lv2: 'verbose_name'
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
      title: 'Свободно (Мб)',
      property: 'free_space',
      type: 'string',
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
    }
  ];
  public collection_vms = [
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
  public node_id: string;
  public menuActive: string = 'info';
  private address: string;

  public host: boolean = false;
  private sub: Subscription;

  constructor(private activatedRoute: ActivatedRoute,
              private service: NodesService,
              private router: Router) { }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.node_id = param.get('id');
      this.address = param.get('address');
      this.getNode();
    });
  }

  public getNode() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
    this.host = false;
    this.sub = this.service.getNode(this.node_id, this.address).valueChanges.pipe(map(data => data.data.node))
      .subscribe((data) => {
        this.node = data;
        this.host = true;
      },
        () => {
          this.host = true;
        });
  }

  public routeTo(route: string): void {
    if (route === 'info') {
      this.menuActive = 'info';
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

  public close() {
    this.router.navigate(['pages/resourses/nodes']);
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }

}
