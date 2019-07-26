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
  public spinner:boolean = false;
  private pageHeightMinNumber: number = 315;
	private pageHeightMin: string = '315px';
	private pageHeightMax: string = '100%';
  private pageHeight: string = '100%';
  private pageRollup: boolean = false;
  private getPoolsSub: Subscription;

  public collection: object[] = [
    {
      title: 'Название',
      property: 'name',
      class: 'name-start'
    },
    {
      title: 'Начальное количество ВМ',    // всего вм
      property: 'settings',
      property_lv2: 'initial_size'
    },
    {
      title: 'Количество создаваемых ВМ',      // сколько свободных осталось
      property: 'settings',
      property_lv2: 'reserve_size'
    },
    {
      title: 'Доступные ВМ',
      property: 'state',
      property_lv2_array: 'available'
    }
  ];


  constructor(private service: PoolsService,public dialog: MatDialog,private router: Router){}

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
    this.getAllPools();
  }

  public openCreatePool() {
    this.dialog.open(PoolAddComponent, {
      width: '500px'
    });
  }

  private getAllPools() {
    this.spinner = true;
    this.getPoolsSub = this.service.getAllPools(true)
      .subscribe( (data) => {
        console.log('ss');
        this.pools = data;
        this.spinner = false;
      },
      (error) => {
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
    this.router.navigate([`pools/${event.id}`]);

    setTimeout(()=>{
      this.pageHeight = this.pageHeightMin;
    }, 0);
  }

  ngOnDestroy() {
    this.getPoolsSub.unsubscribe();
  }

}
