
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
  private sub: Subscription;

  public host: boolean = false;

  public node: type_node = {};

  public collection = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string'
    },
    {
      title: 'Описание',
      property: 'description',
      type: 'string'
    },
    {
      title: 'Локация',
      property: 'datacenter_name',
      type: 'string'
    },
    {
      title: 'Кластер',
      property: 'cluster_name',
      type: 'string'
    },
    {
      title: 'IP-адрес',
      property: 'management_ip',
      type: 'string'
    },
    {
      title: 'Оперативная память (Мб)',
      property: 'memory_count',
      type: 'string'
    },
    {
      title: 'CPU',
      property: 'cpu_count',
      type: 'string'
    },
    {
      property: 'node_plus_controller_installation',
      title: 'Тип установки',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Veil controller + Veil server', 'Veil server']
      }
    },
    {
      title: 'Статус',
      property: 'status'
    }
  ];

  public node_id: string;
  public menuActive: string = 'info';
  private address: string;

  filter: object

  constructor(private activatedRoute: ActivatedRoute,
              private service: NodesService,
              private router: Router) { }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.node_id = param.get('id');
      this.address = param.get('address');
      this.getNode();

      this.filter = {
        controller_id: this.address,
        node_id: this.node_id
      }
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
    this.menuActive = route
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
