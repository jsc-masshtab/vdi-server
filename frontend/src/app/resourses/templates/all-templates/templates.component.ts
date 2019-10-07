import { WaitService } from './../../../common/components/single/wait/wait.service';
import { Component, OnInit } from '@angular/core';
import { TemplatesService } from './templates.service';
import { map } from 'rxjs/operators';


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

  constructor(private service: TemplatesService, private waitService: WaitService){}

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


}
