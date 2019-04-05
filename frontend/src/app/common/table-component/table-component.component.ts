import { Component, OnInit, Input, OnChanges} from '@angular/core';

@Component({
  selector: 'vdi-table-component',
  templateUrl: './table-component.component.html',
  styleUrls: ['./table-component.component.scss']
})
export class TableComponentComponent  {

  @Input() data: object[] = [];
	@Input() collection: object[] = [];

  constructor() {}

  
}
