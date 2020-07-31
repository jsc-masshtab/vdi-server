import { IParams } from '../../../../../../types';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { Component, OnInit, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { NodesService } from './nodes.service';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';
import { DetailsMove } from 'src/app/dashboard/common/classes/details-move';
import { Subscription } from 'rxjs';

@Component({
  selector: 'vdi-nodes',
  templateUrl: './nodes.component.html',
  styleUrls: ['./nodes.component.scss']
})


export class NodesComponent extends DetailsMove implements OnInit, OnDestroy {

  public infoTemplates: [];
  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'server',
      sort: true
    },
    {
      title: 'Локация',
      property: 'datacenter_name',
      type: 'string',
      sort: true
    },
    {
      title: 'IP-адрес',
      property: 'management_ip',
      type: 'string',
      sort: true
    },
    {
      title: 'CPU',
      property: 'cpu_count',
      type: 'string',
      sort: true
    },
    {
      title: 'RAM',
      property: 'memory_count',
      type: 'string',
      sort: true
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

  public nodes: object[] = [];
  private sub: Subscription;

  constructor(private service: NodesService, private router: Router, private waitService: WaitService) {
    super();
  }

  @ViewChild('view') view: ElementRef;

  ngOnInit() {
    this.getNodes();
  }

  public getNodes() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
    this.waitService.setWait(true);
    this.sub = this.service.getAllNodes().valueChanges.pipe(map(data => data.data.nodes))
      .subscribe((data) => {
        this.nodes = data;
        this.waitService.setWait(false);
      });
  }

  public routeTo(event): void {
    this.router.navigate([`pages/resourses/nodes/${event.controller.id}/${event.id}`]);
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

  public sortList(param: IParams): void  {
    this.service.paramsForGetNodes.spin = param.spin;
    this.service.paramsForGetNodes.nameSort = param.nameSort;
    this.getNodes();
  }

  ngOnDestroy() {
    this.service.paramsForGetNodes.spin = true;
    this.service.paramsForGetNodes.nameSort = undefined;
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }

}
