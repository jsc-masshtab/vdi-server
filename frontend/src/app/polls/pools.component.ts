import { WaitService } from './../common/components/wait/wait.service';
import { Component, OnInit, HostListener,ViewChild,ElementRef} from '@angular/core';
import { PoolsService } from './pools.service';
import { PoolAddComponent } from './pool-add/pool-add.component';
import { Router } from '@angular/router';
import { MatDialog } from '@angular/material';
import { Subscription } from 'rxjs';


@Component({
  selector: 'vdi-pools',
  templateUrl: './pools.component.html',
  styleUrls: ['./pools.component.scss']
})

export class PoolsComponent implements OnInit {

  public pools: [];
  public pageHeightMinNumber: number = 315;
	public pageHeightMin: string = '315px';
	public pageHeightMax: string = '100%';
  public pageHeight: string = '100%';
  public pageRollup: boolean = false;
  private getPoolsSub: Subscription;

  public collection: object[] = [
    {
      title: '№',
      property: 'index'
    },
    {
      title: 'Название',
      property: 'name',
      class: 'name-start',
      icon: 'desktop'
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'ip'
    },
    {
      title: 'Доступные ВМ',
      property_array: 'vms'
    },
    {
      title: 'Тип',
      property: 'desktop_pool_type'
    }
  ];

  constructor(private service: PoolsService,public dialog: MatDialog,private router: Router,private waitService: WaitService){}

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
    this.getAllPools({spin:true});
  }

  public openCreatePool() {
    this.dialog.open(PoolAddComponent, {
      width: '500px'
    });
  }

  public getAllPools(spin?:{}) {
    if(spin && spin['spin']) {
      this.waitService.setWait(true);
    }
    this.getPoolsSub = this.service.getAllPools({obs:true})
      .subscribe( (data) => {
        this.pools = data;
        if(spin && spin['spin']) {
          this.waitService.setWait(false);
        }
      });
  }

  public componentAdded(): void {
		setTimeout(()=> {
		//	this.routerActivated = true;
			this.pageHeight = this.pageHeightMin;

			if((this.view.nativeElement.clientHeight - this.pageHeightMinNumber) < (this.pageHeightMinNumber + 250)) {
				this.pageRollup = true;
			};
		}, 0);
	}

  public componentRemoved(): void {
		setTimeout(()=> {
			//this.routerActivated = false;
			this.pageHeight = this.pageHeightMax;
			this.pageRollup = false;
		}, 0);
  }

  public routeTo(event): void {
    let desktop_pool_type:string = event.desktop_pool_type.toLowerCase();
    this.router.navigate([`pools/${desktop_pool_type}/${event.id}`]);

    setTimeout(() => {
      this.pageHeight = this.pageHeightMin;
    }, 0);
  }

  ngOnDestroy() {
    this.getPoolsSub.unsubscribe();
  }

}
