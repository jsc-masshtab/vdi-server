import { DetailsMove } from '../../../common/classes/details-move';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { ClustersService } from './clusters.service';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';

@Component({
  selector: 'vdi-clusters',
  templateUrl: './clusters.component.html',
  styleUrls: ['./clusters.component.scss']
})


export class ClustersComponent extends DetailsMove implements OnInit {

  public clusters = [];
  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'building'
    },
    {
      title: 'Серверы',
      property: 'nodes_count',
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
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'ip'
    },
    {
      title: 'Статус',
      property: 'status'
    }
  ];


  constructor(private service: ClustersService, private router: Router, private waitService: WaitService) {
    super();
  }

  @ViewChild('view') view: ElementRef;

  ngOnInit() {
    this.getAllClusters();
  }

  public getAllClusters(): void {
    this.waitService.setWait(true);
    this.service.getAllClusters().valueChanges.pipe(map(data => data.data.controllers))
      .subscribe((data) => {
        let arrClusters: [][] = [];
        this.clusters = [];
        arrClusters = data.map(controller => controller.clusters);

        arrClusters.forEach((arr: []) => {
          arr.forEach((obj: {}) => {
            this.clusters.push(obj);
          });
        });
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
    this.router.navigate([`resourses/clusters/${event.id}`]);
  }

}
