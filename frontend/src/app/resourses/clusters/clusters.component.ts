import { Component, OnInit,HostListener,ViewChild,ElementRef } from '@angular/core';
import { ClustersService } from './clusters.service';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';

@Component({
  selector: 'vdi-clusters',
  templateUrl: './clusters.component.html',
  styleUrls: ['./clusters.component.scss']
})


export class ClustersComponent implements OnInit {

  public clusters: object[] = [];
  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start'
    },
    {
      title: 'Серверы',
      property: "nodes_count"
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

  public spinner:boolean = false;

  private pageHeightMinNumber: number = 315;
	private pageHeightMin: string = '315px';
	private pageHeightMax: string = '100%';
  private pageHeight: string = '100%';
  private pageRollup: boolean = false;

  constructor(private service: ClustersService,private router: Router){}


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
    this.getAllClusters();
  }

  private getAllClusters() {
    this.spinner = true;
    this.service.getAllClusters().valueChanges.pipe(map(data => data.data.clusters))
      .subscribe( (data) => {
        this.clusters = data;
        this.spinner = false;
      },
      (error)=> {
        this.spinner = false;
      });
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

  public routeTo(event): void {
    this.router.navigate([`resourses/clusters/${event.id}`]);

    setTimeout(()=> {
      this.pageHeight = this.pageHeightMin;
    }, 0);
  }


}
