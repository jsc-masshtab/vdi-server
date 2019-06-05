import { Component, Input } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'vdi-breadcrumbs',
  templateUrl: './breadcrumbs.component.html',
  styleUrls: ['./breadcrumbs.component.scss']
})
export class BreadcrumbsComponent  {

  @Input() data: object[];

  constructor(private router: Router) {}

  public routeTo(crumb,index) {
    if(index === 0 || !crumb.route) {
      return;
    }
    this.router.navigate([crumb.route]);
  }

}
