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
      class: 'name-start'
    },
    {
      title: 'Cервер',
      property: "node",
      property_lv2: 'verbose_name'
    },
    {
      title: 'Оперативная память (MБ)',
      property: 'memory_count'
    },
    {
      title: 'Высокая доступность',
      property_boolean: 'ha_enabled',
      property_boolean_true: 'Включена',
      property_boolean_false: 'Выключена'
    },
    {
      title: 'Статус',
      property: "status"
    }
  ];


  public spinner:boolean = false;

  constructor(private service: TemplatesService){}

  ngOnInit() {
    this.getTemplates();
  }

  public getTemplates() {
    this.spinner = true;
    this.service.getAllTemplates().valueChanges.pipe(map(data => data.data.controllers)).subscribe((data)=> {
       let arrTemplates: [][] = [];
        this.templates = [];
        arrTemplates = data.map(controller => controller.templates);

        arrTemplates.forEach((arr: []) => {
            arr.forEach((obj: {}) => {
              this.parseInfoTmp(obj);
            }); 
        });
   
    this.spinner = false;
    },(error) => {
      this.spinner = false;
    });
  }

  private parseInfoTmp(info): void {
    this.templates.push(JSON.parse(info['info']));
  }


}
