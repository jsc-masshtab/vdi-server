import { WaitService } from './../../common/components/wait/wait.service';
import { Component, OnInit, HostListener, ViewChild, ElementRef } from '@angular/core';
import { ClustersService } from './clusters.service';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';

@Component({
  selector: 'vdi-clusters',
  templateUrl: './clusters.component.html',
  styleUrls: ['./clusters.component.scss']
})


export class ClustersComponent implements OnInit {

  public clusters = [];
  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start'
    },
    {
      title: 'Серверы',
      property: 'nodes_count'
    },
    {
      title: 'CPU',
      property: 'cpu_count'
    },
    {
      title: 'RAM',
      property: 'memory_count'
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

  public pageHeightMinNumber: number = 315;
  public pageHeightMin: string = '315px';
  public pageHeightMax: string = '100%';
  public pageHeight: string = '100%';
  public pageRollup: boolean = false;

  constructor(private service: ClustersService, private router: Router, private waitService: WaitService) { }

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
    this.getAllClusters();
  }

  public getAllClusters() {
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

  public componentAdded(): void {
    setTimeout(() => {
      //	this.routerActivated = true;
      this.pageHeight = this.pageHeightMin;

      if ((this.view.nativeElement.clientHeight - this.pageHeightMinNumber) < (this.pageHeightMinNumber + 250)) {
        this.pageRollup = true;
      };
    }, 0);
  }

  public componentRemoved(): void {
    setTimeout(() => {
      //this.routerActivated = false;
      this.pageHeight = this.pageHeightMax;
      this.pageRollup = false;
    }, 0);
  }

  public routeTo(event): void {
    this.router.navigate([`resourses/clusters/${event.id}`]);

    setTimeout(() => {
      this.pageHeight = this.pageHeightMin;
    }, 0);
  }


}
