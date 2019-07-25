import { Component, OnInit, HostListener,ViewChild,ElementRef } from '@angular/core';
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
      property: "datacenter_name"
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

  public spinner:boolean = false;

  private pageHeightMinNumber: number = 315;
	private pageHeightMin: string = '315px';
	private pageHeightMax: string = '100%';
  private pageHeight: string = '100%';
  private pageRollup: boolean = false;

  constructor(private service: NodesService,private router: Router){}

  @ViewChild('view') view:ElementRef;

  @HostListener('window:resize', ['$event']) onResize(event) {
		if(this.pageHeight == this.pageHeightMin) {
			if((this.view.nativeElement.clientHeight - this.pageHeightMinNumber) < (this.pageHeightMinNumber + 250)) {
				this.pageRollup = true;
			} else {
				this.pageRollup = false;
			}
		}
	}

  ngOnInit() {
    this.getNodes();
  }

  private getNodes() {
    this.spinner = true;
    this.service.getAllNodes().valueChanges.pipe(map(data => data.data.controllers))
      .subscribe( (data) => {
        this.nodes = data;
        let arrsNodes: [][] = [];
        this.nodes = [];
        arrsNodes = data.map(controller => controller.nodes);

        arrsNodes.forEach((arr: []) => {
            arr.forEach((obj: {}) => {
              this.nodes.push(obj);
            }); 
        });
        this.spinner = false;
      },
      (error)=> {
        this.spinner = false;
      });
  }

  public routeTo(event): void {
    this.router.navigate([`resourses/nodes/${event.id}`]);

    setTimeout(()=> {
      this.pageHeight = this.pageHeightMin;
    }, 0);
  }

  private componentAdded(): void {
		setTimeout(()=> {
		//	this.routerActivated = true;
			this.pageHeight = this.pageHeightMin;

			if((this.view.nativeElement.clientHeight - this.pageHeightMinNumber) < (this.pageHeightMinNumber + 250)) {
				this.pageRollup = true;
			};
		}, 0);
	}

	private componentRemoved(): void {
		setTimeout(()=> {
			//this.routerActivated = false;
			this.pageHeight = this.pageHeightMax;
			this.pageRollup = false;
		}, 0);
  }

}
