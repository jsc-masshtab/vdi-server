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
  private sub: Subscription;

  public host: boolean = false;

  public cluster: ICollection = {};
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
  public idCluster: string;
  public menuActive: string = 'info';
  private address: string;

  filter: object

  constructor(private activatedRoute: ActivatedRoute,
              private service: ClustersService,
              private router: Router) { }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.idCluster = param.get('id');
      this.address = param.get('address');
      this.getCluster();

      this.filter = {
        controller_id: this.address,
        cluster_id: this.idCluster
      }
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
    this.menuActive = route
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }


}
