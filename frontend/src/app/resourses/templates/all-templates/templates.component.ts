import { WaitService } from './../../../common/components/single/wait/wait.service';
import { Component, OnInit, HostListener, ViewChild, ElementRef } from '@angular/core';
import { TemplatesService } from './templates.service';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';


@Component({
  selector: 'vdi-templates',
  templateUrl: './templates.component.html',
  styleUrls: ['./templates.component.scss']
})


export class TemplatesComponent implements OnInit {

  public templates: object[] = [];
  public collection = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'tv'
    },
    {
      title: 'Cервер',
      property: 'node',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Оперативная память (MБ)',
      property: 'memory_count',
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

  constructor(private service: TemplatesService, private waitService: WaitService,  private router: Router) {}

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
    this.getTemplates();
  }

  public getTemplates() {
    this.waitService.setWait(true);
    this.service.getAllTemplates().valueChanges.pipe(map(data => data.data.controllers)).subscribe((data) => {
      let arrTemplates: [][] = [];
      this.templates = [];
      arrTemplates = data.map(controller => controller.templates);

      arrTemplates.forEach((arr: []) => {
          arr.forEach((obj: {}) => {
            this.parseInfoTmp(obj);
          });
      });
      this.waitService.setWait(false);
    });
  }

  private parseInfoTmp(info): void {
    this.templates.push(JSON.parse(info['info']));
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
    this.router.navigate([`resourses/templates/${event.id}`]);

    setTimeout(() => {
      this.pageHeight = this.pageHeightMin;
    }, 0);
  }
}
