import { WaitService } from './../../../common/components/single/wait/wait.service';
import { Component, OnInit, ViewChild, ElementRef, HostListener } from '@angular/core';
import { DatapoolsService } from './datapools.service';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';


@Component({
  selector: 'vdi-datapools',
  templateUrl: './datapools.component.html',
  styleUrls: ['./datapools.component.scss']
})


export class DatapoolsComponent implements OnInit {

  public datapools: object[] = [];
  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'folder-open'
    },
    {
      title: 'Тип',
      property: 'type',
      type: 'string'
    },
    {
      title: 'Диски',
      property: 'vdisk_count',
      type: 'string'
    },
    {
      title: 'Образы',
      property: 'iso_count',
      type: 'string'
    },
    {
      title: 'Файлы',
      property: 'file_count',
      type: 'string'
    },
    {
      title: 'Свободно (Мб)',
      property: 'free_space',
      type: 'string'
    },
    {
      title: 'Занято (Мб)',
      property: 'used_space',
      type: 'string'
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

  constructor(private service: DatapoolsService, private waitService: WaitService,  private router: Router) {}

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
    this.getDatapools();
  }

  public getDatapools() {
    this.waitService.setWait(true);
    this.service.getAllDatapools().valueChanges.pipe(map(data => data.data.controllers))
      .subscribe( (data) => {
        let arrDatapools: [][] = [];
        this.datapools = [];
        arrDatapools = data.map(controller => controller.datapools);

        arrDatapools.forEach((arr: []) => {
            arr.forEach((obj: {}) => {
              this.datapools.push(obj);
            });
        });
        this.waitService.setWait(false);
      });
  }

  public componentAdded(): void {
    setTimeout(() => {
      this.pageHeight = this.pageHeightMin;

      if ((this.view.nativeElement.clientHeight - this.pageHeightMinNumber) < (this.pageHeightMinNumber + 250)) {
        this.pageRollup = true;
      }
    }, 0);
  }

  public componentRemoved(): void {
    setTimeout(() => {
      this.pageHeight = this.pageHeightMax;
      this.pageRollup = false;
    }, 0);
  }

  public routeTo(event): void {
    this.router.navigate([`resourses/datapools/${event.id}`]);

    setTimeout(() => {
      this.pageHeight = this.pageHeightMin;
    }, 0);
  }

}
