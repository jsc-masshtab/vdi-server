import { DatapoolsService } from '../all-datapools/datapools.service';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

interface ICollection {
  [index: string]: string;
}

@Component({
  selector: 'vdi-datapool-details',
  templateUrl: './datapool-details.component.html',
  styleUrls: ['./datapool-details.component.scss']
})


export class DatapoolDetailsComponent implements OnInit, OnDestroy {
  private sub: Subscription;
  public host: boolean = false;

  public datapool: ICollection = {};

  public collectionDetails = [
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
      title: 'Свободно (МБ)',
      property: 'free_space',
      type: 'string'
    },
    {
      title: 'Занято (МБ)',
      property: 'used_space',
      type: 'string'
    },
    {
      title: 'Серверы',
      property: 'nodes_connected',
      type: 'array-length'
    },
    {
      title: 'Статус',
      property: 'status',
      type: 'string'
    }
  ];

  public idDatapool: string;
  private address: string;

  public menuActive: string = 'info';

  filter: object

  constructor(private activatedRoute: ActivatedRoute,
              private service: DatapoolsService,
              private router: Router) { }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.idDatapool = param.get('id') as string;
      this.address = param.get('address');
      this.getDatapool();

      this.filter = {
        controller_id: this.address,
        data_pool_id: this.idDatapool
      }
    });
  }

  public getDatapool() {
    if (this.sub) {
      this.sub.unsubscribe();
    }

    this.host = false;
    this.sub = this.service.getDatapool(this.idDatapool, this.address).valueChanges.pipe(map(data => data.data.datapool))
      .subscribe((data) => {
        this.datapool = data;
        this.host = true;
      },
      () => {
        this.host = true;
      });
  }

  public close() {
    this.router.navigate(['pages/resourses/datapools']);
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
