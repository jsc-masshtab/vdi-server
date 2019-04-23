import { Component, OnInit, Input } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'vdi-breadcrumbs',
  templateUrl: './breadcrumbs.component.html',
  styleUrls: ['./breadcrumbs.component.scss']
})
export class BreadcrumbsComponent implements OnInit {

  @Input() data: object[];

  constructor(private router: Router) {}

  ngOnInit() {
    console.log(this.data);
  }

  la(crumb) {
    console.log(crumb);
    this.router.navigate([crumb.route]);
  }

}
