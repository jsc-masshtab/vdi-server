import { TemplatesService } from '../all-templates/templates.service';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

interface ICollection {
  [index: string]: string;
}


@Component({
  selector: 'vdi-template-details',
  templateUrl: './template-details.component.html',
  styleUrls: ['./template-details.component.scss']
})


export class TemplateDetailsComponent implements OnInit, OnDestroy {

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
  private address: string;
  private sub: Subscription;

  constructor(private activatedRoute: ActivatedRoute,
              private service: TemplatesService,
              private router: Router) { }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.idTemplate = param.get('id') as string;
      this.address = param.get('address') as string;
      this.getTemplate();
    });
  }

  public getTemplate() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
    this.host = false;
    this.sub = this.service.getTemplate(this.idTemplate, this.address).valueChanges.pipe(map(data => data.data.template))
      .subscribe((data) => {
        this.template = JSON.parse(data['veil_info_json']);
        this.host = true;
      },
      () => {
        this.host = true;
      });
  }

  public close() {
    this.router.navigate(['pages/resourses/templates']);
  }

  public routeTo(route: string): void {
    if (route === 'info') {
      this.menuActive = 'info';
    }
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }
}
