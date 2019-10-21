import { WaitService } from './../../../common/components/single/wait/wait.service';
import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { NodesService } from './nodes.service';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';
import { DetailsMove } from 'src/app/common/classes/details-move';

@Component({
  selector: 'vdi-nodes',
  templateUrl: './nodes.component.html',
  styleUrls: ['./nodes.component.scss']
})


export class NodesComponent extends DetailsMove implements OnInit {

  public infoTemplates: [];
  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'server'
    },
    {
      title: 'Локация',
      property: 'datacenter_name',
      type: 'string'
    },
    {
      title: 'IP-адрес',
      property: 'management_ip',
      type: 'string'
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
      title: 'Статус',
      property: 'status'
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
    this.service.getAllNodes().valueChanges.pipe(map(data => data.data.controllers))
      .subscribe((data) => {
        this.nodes = [];
        let arrNodes: [][] = [];

        arrNodes = data.map(controller => controller.nodes);

        arrNodes.forEach((arr: []) => {
          arr.forEach((obj: {}) => {
            this.nodes.push(obj);
          });
        });
        this.waitService.setWait(false);
      });
  }

  public routeTo(event): void {
    this.router.navigate([`resourses/nodes/${event.id}`]);
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

}
