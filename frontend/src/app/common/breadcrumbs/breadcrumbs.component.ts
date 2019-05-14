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
    console.log(crumb,index);
    if(index === 0) {
      return;
    }
    console.log(crumb.route);
    this.router.navigate([crumb.route]);
  }

}
