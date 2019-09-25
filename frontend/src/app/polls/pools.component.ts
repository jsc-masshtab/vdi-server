import { WaitService } from './../common/components/wait/wait.service';
import { Component, OnInit, HostListener, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { PoolsService } from './pools.service';
import { PoolAddComponent } from './pool-add/pool-add.component';
import { Router } from '@angular/router';
import { MatDialog } from '@angular/material';
import { Subscription } from 'rxjs';


@Component({
  selector: 'vdi-pools',
  templateUrl: './pools.component.html',
  styleUrls: ['./pools.component.scss']
})

export class PoolsComponent implements OnInit, OnDestroy {

  public pools: [];
  public pageHeightMinNumber: number = 315;
  public pageHeightMin: string = '315px';
  public pageHeightMax: string = '100%';
  public pageHeight: string = '100%';
  public pageRollup: boolean = false;
  private getPoolsSub: Subscription;

  public collection: ReadonlyArray<object> = [
    {
      title: '№',
      property: 'index'
    },
    {
      title: 'Название',
      property: 'name',
      class: 'name-start',
      icon: 'desktop'
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'ip'
    },
    {
      title: 'Доступные ВМ',
      property_array: 'vms'
    },
    {
      title: 'Пользователи',
      property_array_prop: 'users',
      property_array_prop_lv2: 'username'
    },
    {
      title: 'Тип',
      property: 'desktop_pool_type'
    }
  ];

  constructor(private service: PoolsService, public dialog: MatDialog, private router: Router, private waitService: WaitService) {}

  @ViewChild('view') view: ElementRef;

  @HostListener('window:resize', ['$event']) onResize() {
    if (this.pageHeight === this.pageHeightMin) {
      if ((this.view.nativeElement.clientHeight - this.pageHeightMinNumber) < (this.pageHeightMinNumber + 250)) {
        this.pageRollup = true;
      } else {
        this.pageRollup = false;
      }
    }
  }

  ngOnInit() {
    this.getAllPools({ spin: true, obs: true });
  }

  public openCreatePool(): void {
    this.dialog.open(PoolAddComponent, {
      width: '500px'
    });
  }

  public getAllPools(param?: { readonly spin?: boolean,  readonly obs?: boolean }): void {
    if (param && param.spin) {
      this.waitService.setWait(true);
    }
    this.getPoolsSub = this.service.getAllPools(param.obs)
      .subscribe((data) => {
        this.pools = data;
        if (param && param.spin) {
          this.waitService.setWait(false);
          param = {};
        }
      });
  }

  public componentAdded(): void {
    setTimeout(() => {
      this.pageHeight = this.pageHeightMin;

      if ((this.view.nativeElement.clientHeight - this.pageHeightMinNumber) < (this.pageHeightMinNumber + 250)) {
        this.pageRollup = true;
      }
    }, 0);
  }

  public componentRemoved(): void {
    setTimeout(() => {
      this.pageHeight = this.pageHeightMax;
      this.pageRollup = false;
    }, 0);
  }

  public routeTo(event): void {
    const desktopPoolType: string = event.desktop_pool_type.toLowerCase();
    this.router.navigate([`pools/${desktopPoolType}/${event.id}`]);

    setTimeout(() => {
      this.pageHeight = this.pageHeightMin;
    }, 0);
  }

  ngOnDestroy() {
    this.getPoolsSub.unsubscribe();
  }

}
