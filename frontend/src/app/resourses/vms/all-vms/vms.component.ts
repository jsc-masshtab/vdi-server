import { Component, OnInit, ViewChild, ElementRef, HostListener } from '@angular/core';
import { VmsService } from './vms.service';
import { map } from 'rxjs/operators';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { Router } from '@angular/router';

@Component({
  selector: 'vdi-vms',
  templateUrl: './vms.component.html',
  styleUrls: ['./vms.component.scss']
})


export class VmsComponent implements OnInit {

  public vms: object[] = [];
  public collection = [
    {
      title: 'Название',
      property: 'name',
      class: 'name-start',
      icon: 'desktop',
      type: 'string'
    },
    {
      title: 'Сервер',
      property: 'node',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Шаблон',
      property: 'template',
      property_lv2: 'name'
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

  constructor(private service: VmsService, private waitService: WaitService, private router: Router) {}

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
    this.getAllVms();
  }

  public getAllVms() {
    this.waitService.setWait(true);
    this.service.getAllVms().valueChanges.pipe(map(data => data.data.controllers)).subscribe((data) => {
      let arrVms: [][] = [];
      this.vms = [];
      arrVms = data.map(controller => controller.vms);

      arrVms.forEach((arr: []) => {
          arr.forEach((obj: {}) => {
            this.vms.push(obj);
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
    this.router.navigate([`resourses/vms/${event.id}`]);

    setTimeout(() => {
      this.pageHeight = this.pageHeightMin;
    }, 0);
  }
}
