import { IParams } from './../../../../../types/index.d';
import { WaitService } from './../../../common/components/single/wait/wait.service';
import { Component, OnInit, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { NodesService } from './nodes.service';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';
import { DetailsMove } from 'src/app/common/classes/details-move';

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
      reverse_sort: true
    },
    {
      title: 'Локация',
      property: 'datacenter_name',
      type: 'string',
      reverse_sort: true
    },
    {
      title: 'IP-адрес',
      property: 'management_ip',
      type: 'string',
      reverse_sort: true
    },
    {
      title: 'CPU',
      property: 'cpu_count',
      type: 'string',
      reverse_sort: true
    },
    {
      title: 'RAM',
      property: 'memory_count',
      type: 'string',
      reverse_sort: true
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'address',
      reverse_sort: true
    },
    {
      title: 'Статус',
      property: 'status',
      reverse_sort: true
    }
  ];

  public nodes: object[] = [];

  constructor(private service: NodesService, private router: Router, private waitService: WaitService) {
    super();
  }

  @ViewChild('view') view: ElementRef;

  ngOnInit() {
    this.getNodes();
  }

  public getNodes() {
    this.waitService.setWait(true);
    this.service.getAllNodes().valueChanges.pipe(map(data => data.data.nodes))
      .subscribe((data) => {
        this.nodes = data;
        this.waitService.setWait(false);
      });
  }

  public routeTo(event): void {
    this.router.navigate([`resourses/nodes/${event.controller.address}/${event.id}`]);
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
    this.service.paramsForGetNodes.reverse = param.reverse;
    this.getNodes();
  }

  ngOnDestroy() {
    this.service.paramsForGetNodes.spin = true;
    this.service.paramsForGetNodes.nameSort = undefined;
    this.service.paramsForGetNodes.reverse = undefined;
  }

}
