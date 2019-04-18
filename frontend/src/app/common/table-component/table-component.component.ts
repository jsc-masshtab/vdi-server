import { Component, OnInit, Input, OnChanges, Output,  EventEmitter} from '@angular/core';


@Component({
  selector: 'vdi-table-component',
  templateUrl: './table-component.component.html',
  styleUrls: ['./table-component.component.scss']
})
export class TableComponentComponent  {

  public clickRowNow:boolean = false;

  @Input() data: object[] = [];
  @Input() collection: object[] = [];
  @Input() empty: string = 'Ничего нет';
  @Output() clickRowData:EventEmitter<any> = new EventEmitter();

  constructor() {}



  public clickRow(item) {
    this.clickRowNow = true;
    this.clickRowData.emit(item);
  }

  
}
