import { WaitService } from './../../../common/components/single/wait/wait.service';
import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { TemplatesService } from './templates.service';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';
import { DetailsMove } from 'src/app/common/classes/details-move';


@Component({
  selector: 'vdi-templates',
  templateUrl: './templates.component.html',
  styleUrls: ['./templates.component.scss']
})


export class TemplatesComponent extends DetailsMove implements OnInit {

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

  constructor(private service: TemplatesService, private waitService: WaitService,  private router: Router) {
    super();
  }

  @ViewChild('view') view: ElementRef;


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

  public routeTo(event): void {
    this.router.navigate([`resourses/templates/${event.id}`]);
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
}
