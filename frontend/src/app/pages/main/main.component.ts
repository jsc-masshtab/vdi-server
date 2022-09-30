import { Component, OnDestroy, OnInit } from '@angular/core';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { MainService } from './main.service';

@Component({
  selector: 'vdi-main',
  templateUrl: './main.component.html',
  styleUrls: ['./main.component.scss']
})
export class MainComponent implements OnInit, OnDestroy {

  private destroy: Subject<any> = new Subject<any>();

  clients: any[] = [];
  controllers: any[] = [];
  about: any = {}

  automated: any = {
    count: 0,
    vms: 0,
    users: 0
  }
  static: any = {
    count: 0,
    vms: 0,
    users: 0
  }
  guest: any = {
    count: 0,
    vms: 0,
    users: 0
  }
  rds: any = {
    count: 0,
    vms: 0,
    users: 0
  }

  public collectionAbout: any[] = [
    {
      title: 'Брокер',
      property: 'verbose_name',
      type: 'string'
    },
    {
      title: 'Компания',
      property: 'company',
      type: 'string'
    },
    {
      title: 'Версия брокера',
      property: 'version',
      type: 'string'
    },
    {
      title: 'Минимальная версия тонкого клиента',
      property: 'version_client',
      type: 'string'
    },
    {
      title: 'Доступно тонких клиентов',
      property: 'thin_clients_limit',
      type: 'string'
    },
    {
      title: 'Активных тонких клиентов',
      property: 'thin_clients_count',
      type: 'string'
    }
  ];

  constructor(
    private service: MainService
  ) {}

  ngOnInit() {
    this.service.getVersionClientInfo().valueChanges.pipe(takeUntil(this.destroy)).subscribe((res: any) => {
      this.about['version_client'] = res.data.version_client;
      this.about = { ...this.about };
    });

    this.service.getControllersInfo().valueChanges.pipe(takeUntil(this.destroy)).subscribe((res: any) => {
      this.controllers = res.data.controllers || [];
    });

    this.service.getPoolsInfo().valueChanges.pipe(takeUntil(this.destroy)).subscribe((res: any) => {

      const pools = res.data.pools;

      pools.forEach((pool: any) => {
        const type = String(pool.pool_type).toLowerCase();
        this[type].count ++;
        this[type].vms += pool.vm_amount;
        this[type].users += pool.users_count;
      });
    });

    this.service.getLicence().pipe(takeUntil(this.destroy)).subscribe((res: any) => {
      this.about['verbose_name'] = res.data.verbose_name;
      this.about['company'] = res.data.company;
      this.about['thin_clients_limit'] = res.data.thin_clients_limit;
      this.about['thin_clients_count'] = res.data.thin_clients_count;
      this.about = { ...this.about };
    });

    this.service.getVersionInfo().pipe(takeUntil(this.destroy)).subscribe((res: any) => {
      this.about['version'] = res.data.version;
      this.about = { ...this.about };
    });
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }
}
