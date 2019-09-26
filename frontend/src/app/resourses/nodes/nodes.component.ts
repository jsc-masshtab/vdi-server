import { WaitService } from './../../common/components/wait/wait.service';
import { Component, OnInit, HostListener, ViewChild, ElementRef } from '@angular/core';
import { NodesService } from './nodes.service';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';

@Component({
  selector: 'vdi-nodes',
  templateUrl: './nodes.component.html',
  styleUrls: ['./nodes.component.scss']
})


export class NodesComponent implements OnInit {

  public infoTemplates: [];
  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start'
    },
    {
      title: 'Локация',
      property: 'datacenter_name'
    },
    {
      title: 'IP-адрес',
      property: 'management_ip'
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
      title: 'Статус',
      property: 'status'
    }
  ];

  public nodes: object[] = [];

  public pageHeightMinNumber: number = 315;
  public pageHeightMin: string = '315px';
  public pageHeightMax: string = '100%';
  public pageHeight: string = '100%';
  public pageRollup: boolean = false;

  constructor(private service: NodesService, private router: Router, private waitService: WaitService) { }

  @ViewChild('view') view: ElementRef;

  @HostListener('window:resize', ['$event']) onResize() {
    if (this.pageHeight == this.pageHeightMin) {
      if ((this.view.nativeElement.clientHeight - this.pageHeightMinNumber) < (this.pageHeightMinNumber + 250)) {
        this.pageRollup = true;
      } else {
        this.pageRollup = false;
      }
    }
  }

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

    setTimeout(() => {
      this.pageHeight = this.pageHeightMin;
    }, 0);
  }

  public componentAdded(): void {
    setTimeout(() => {
      this.pageHeight = this.pageHeightMin;

      if ((this.view.nativeElement.clientHeight - this.pageHeightMinNumber) < (this.pageHeightMinNumber + 250)) {
        this.pageRollup = true;
      };
    }, 0);
  }

  public componentRemoved(): void {
    setTimeout(() => {
      this.pageHeight = this.pageHeightMax;
      this.pageRollup = false;
    }, 0);
  }

}
