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
      title: '№',
      property: 'index'
    },
    {
      title: 'Название',
      property: 'verbose_name'
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
    }
  ];

  public crumbs: object[] = [
    {
      title: 'Ресурсы',
      icon: 'database'
    },
    {
      title: `Шаблоны ВМ`,
      icon: 'tv'
    }
  ];

  public spinner:boolean = false;

  constructor(private service: TemplatesService){}

  ngOnInit() {
    this.getTemplates();
  }

  private getTemplates() {
    this.spinner = true;
    this.service.getAllTemplates().valueChanges.pipe(map(data => data.data.templates)).subscribe((res)=> {
      this.templates = res.map((item) => {
        return JSON.parse(item['info']);  
    });
    this.spinner = false;
    },(error) => {
      this.spinner = false;
    });
  }


}
