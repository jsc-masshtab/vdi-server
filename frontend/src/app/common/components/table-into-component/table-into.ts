import { Component,  Input, } from '@angular/core';

@Component({
  selector: 'vdi-table-into',
  templateUrl: './table-into.html',
  styleUrls: ['./table-into.scss']
})
export class TableIntoComponent  {

  @Input() data: {} = {};
  @Input() collection: object[] = [];

  constructor() {}

  
}