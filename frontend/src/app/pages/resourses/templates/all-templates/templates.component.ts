import { Component, OnInit, ViewChild, ElementRef, OnDestroy, Input } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';

import { WaitService } from '@core/components/wait/wait.service';

import { DetailsMove } from '@shared/classes/details-move';
import { IParams } from '@shared/types';

import { TemplatesService } from './templates.service';


@Component({
  selector: 'vdi-templates',
  templateUrl: './templates.component.html',
  styleUrls: ['./templates.component.scss']
})


export class TemplatesComponent extends DetailsMove implements OnInit, OnDestroy {

  @Input() filter: object

  public refresh: boolean = false

  private sub: Subscription;

  public templates: object[] = [];
  public collection = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'tv',
      sort: true
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'verbose_name',
      type: 'string',
      sort: true
    },
    {
      title: 'Статус',
      property: 'status',
      sort: true
    }
  ];

  constructor(private service: TemplatesService, private waitService: WaitService,  private router: Router) {
    super();
  }

  @ViewChild('view', { static: true }) view: ElementRef;

  ngOnInit() {
    this.getTemplates();
  }

  public getTemplates(refresh?) {
    if (this.sub) {
      this.sub.unsubscribe();
    }
    this.waitService.setWait(true);

    let filtered = (data) => {
      if ((this.filter && !this.refresh) || (this.filter && this.refresh)) {
        return data.data.controller.templates
      } else {
        return data.data.templates
      }
    }

    if (refresh) {
      this.refresh = refresh
    }
    this.sub = this.service.getAllTemplates(this.filter, this.refresh).valueChanges.pipe(map(data => filtered(data))).subscribe((data) => {
      this.templates = data;
      this.waitService.setWait(false);
    });
  }

  public routeTo(event): void {

    let id = event.id
    let controller_id = ''

    if (this.filter) {
      controller_id = this.filter['controller_id']
    } else {
      controller_id = event.controller.id;
    }

    this.router.navigate([`pages/resourses/templates/${controller_id}/${id}`]);
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

  public sortList(param: IParams): void {
    this.service.params.spin = param.spin;
    this.service.params.nameSort = param.nameSort;
    this.getTemplates();
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }

}


