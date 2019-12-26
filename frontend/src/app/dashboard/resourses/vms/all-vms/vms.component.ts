import { Component, OnInit, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { VmsService } from './vms.service';
import { map } from 'rxjs/operators';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { Router } from '@angular/router';
import { DetailsMove } from 'src/app/dashboard/common/classes/details-move';
import { Subscription } from 'rxjs';

@Component({
  selector: 'vdi-vms',
  templateUrl: './vms.component.html',
  styleUrls: ['./vms.component.scss']
})


export class VmsComponent extends DetailsMove  implements OnInit, OnDestroy {

  public vms: object[] = [];
  public collection = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'desktop',
      type: 'string'
    },
    {
      title: 'Шаблон',
      property: 'template',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'address'
    },
    {
      title: 'Статус',
      property: 'status'
    }
  ];

  private sub: Subscription;

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
    this.sub = this.service.getAllVms().valueChanges.pipe(map(data => data.data.vms)).subscribe((data) => {
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
    this.router.navigate([`pages/resourses/vms/${event.controller.address}/${event.id}`]);
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }
}
