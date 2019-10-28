import { TemplatesService } from './../all-templates/templates.service';
import { Component, OnInit } from '@angular/core';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { Router } from '@angular/router';

interface ICollection {
  [index: string]: string;
}


@Component({
  selector: 'vdi-template-details',
  templateUrl: './template-details.component.html',
  styleUrls: ['./template-details.component.scss']
})


export class TemplateDetailsComponent implements OnInit {

  public template: ICollection = {};

  public collectionDetails = [
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
    }
  ];

  public idTemplate: string;
  public menuActive: string = 'info';
  public host: boolean = false;

  constructor(private activatedRoute: ActivatedRoute,
              private service: TemplatesService,
              private router: Router) { }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.idTemplate = param.get('id') as string;
      this.getTemplate();
    });
  }

  public getTemplate() {
    this.host = false;
    this.service.getTemplate(this.idTemplate).valueChanges.pipe(map(data => data.data.template))
      .subscribe((data) => {
        this.template = JSON.parse(data['info']);
        this.host = true;
      },
      () => {
        this.host = true;
      });
  }

  public close() {
    this.router.navigate(['resourses/templates']);
  }

  public routeTo(route: string): void {
    if (route === 'info') {
      this.menuActive = 'info';
    }
  }
}
