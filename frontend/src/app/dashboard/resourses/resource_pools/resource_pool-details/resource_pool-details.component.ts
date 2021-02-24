import { Component, OnInit, OnDestroy } from '@angular/core';
import { ResourcePoolsService } from '../all-resource_pools/resource_pools.service';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

interface ICollection {
  [index: string]: string;
}


@Component({
  selector: 'vdi-resource_pool-details',
  templateUrl: './resource_pool-details.component.html',
  styleUrls: ['./resource_pool-details.component.scss']
})


export class ResourcePoolDetailsComponent implements OnInit, OnDestroy {
  private sub: Subscription;

  public host: boolean = false;

  public resource_pool: ICollection = {};
  public collectionDetails: object[] = [
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
      title: 'Ограничение памяти',
      property: 'memory_limit',
      type: 'string'
    },
    {
      title: 'Ограничение CPU',
      property: 'cpu_limit',
      type: 'string'
    },
    {
      title: 'Количество vcpu серверов',
      property: 'nodes_memory_count',
      type: 'string'
    },
    {
      title: 'Количество vcpu ВМ',
      property: 'domains_cpu_count',
      type: 'string'
    },
    {
      title: 'Количество памяти серверов (МБ)',
      property: 'nodes_memory_count',
      type: 'string'
    },
    {
      title: 'Количество памяти ВМ (МБ)',
      property: 'domains_memory_count',
      type: 'string'
    },
  ];
  public idResourcePool: string;
  public menuActive: string = 'info';
  private address: string;

  filter: object

  constructor(private activatedRoute: ActivatedRoute,
              private service: ResourcePoolsService,
              private router: Router) { }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.idResourcePool = param.get('id');
      this.address = param.get('address');
      this.getResourcePool();

      this.filter = {
        controller_id: this.address,
        resource_pool_id: this.idResourcePool
      }
    });
  }

  public getResourcePool() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
    this.host = false;
    this.sub = this.service.getResourcePool(this.idResourcePool, this.address).valueChanges.pipe(map(data => data.data.resource_pool))
      .subscribe((data) => {
        this.resource_pool = data;
        this.host = true;
      },
      () => {
        this.host = true;
      });
  }

  public close() {
    this.router.navigate(['pages/resourses/resource_pools']);
  }

  public routeTo(route: string): void {
    this.menuActive = route
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }


}
