import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';

import { DatapoolsService } from '../all-datapools/datapools.service';

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
  public refresh: boolean = false;

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
      title: 'Описание',
      property: 'description',
      type: 'string'
    },
    {
      title: 'Тип',
      property: 'type',
      type: 'string'
    },
    {
      title: 'Свободно',
      property: 'free_space',
      type: 'bites',
      delimiter: 'Мб'
    },
    {
      title: 'Занято',
      property: 'used_space',
      type: 'bites',
      delimiter: 'Мб'
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

  public getDatapool(refresh?) {
    if (this.sub) {
      this.sub.unsubscribe();
    }

    this.host = false;
    if (refresh) {
      this.refresh = refresh
    }
    this.sub = this.service.getDatapool(this.idDatapool, this.address, this.refresh).valueChanges.pipe(map(data => data.data.datapool))
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
