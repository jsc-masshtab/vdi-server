import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'vdi-breadcrumbs',
  templateUrl: './breadcrumbs.component.html',
  styleUrls: ['./breadcrumbs.component.scss']
})
export class BreadcrumbsComponent implements OnInit {

  @Input() data: object[];

  constructor() {}

  ngOnInit() {
  }

}
