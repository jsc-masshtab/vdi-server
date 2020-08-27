import { Component, OnInit, ViewChild, ElementRef, OnDestroy, Input } from '@angular/core';
import { VmsService } from './vms.service';
import { map } from 'rxjs/operators';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { Router } from '@angular/router';
import { DetailsMove } from 'src/app/dashboard/common/classes/details-move';
import { Subscription } from 'rxjs';
import { IParams } from 'types';

@Component({
  selector: 'vdi-vms',
  templateUrl: './vms.component.html',
  styleUrls: ['./vms.component.scss']
})


export class VmsComponent extends DetailsMove implements OnInit, OnDestroy {
  
  @Input() filter: object

  private sub: Subscription;

  public vms: object[] = [];
  public collection = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'desktop',
      type: 'string',
      sort: true
    },
    {
      title: 'Шаблон',
      property: 'template',
      property_lv2: 'verbose_name',
      type: 'string'
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'verbose_name',
      sort: true
    },
    {
      title: 'Статус',
      property: 'status',
      sort: true
    }
  ];

  constructor(private service: VmsService, private waitService: WaitService, private router: Router) {
    super();
  }

  @ViewChild('view') view: ElementRef;

  ngOnInit() {
    this.getAllVms();
  }

  public getAllVms() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
    this.waitService.setWait(true);

    let filtered = (data) => {
      if (this.filter) {
        return data.data.controller.vms
      } else {
        return data.data.vms
      }
    }

    this.sub = this.service.getAllVms(this.filter).valueChanges.pipe(map(data => filtered(data))).subscribe((data) => {
      this.vms = data;
      this.waitService.setWait(false);
    });
  }

  public onResize(): void {
    super.onResize(this.view);
  }

  public componentActivate(): void {
    super.componentActivate(this.view);
  }

  public componentDeactivate(): void {
    super.componentDeactivate();
  }

  public routeTo(event): void {
    let id = event.id
    let controller_id = ''

    if (this.filter) {
      controller_id = this.filter['controller_id']
    } else {
      controller_id = event.controller.id;
    }

    this.router.navigate([`pages/resourses/vms/${controller_id}/${id}`]);
  }

  public sortList(param: IParams): void {
    this.service.params.spin = param.spin;
    this.service.params.nameSort = param.nameSort;
    this.getAllVms();
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }
}
