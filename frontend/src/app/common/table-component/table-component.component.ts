import { Component,Input, Output, EventEmitter} from '@angular/core';


@Component({
  selector: 'vdi-table-component',
  templateUrl: './table-component.component.html',
  styleUrls: ['./table-component.component.scss']
})
export class TableComponentComponent  {


  @Input() data: object[] = [];
  @Input() spinner:boolean = false;
  @Input() collection: object[] = [];
  @Output() clickRowData:EventEmitter<any> = new EventEmitter();

  constructor() {}

  ngOnChanges() {
    console.log(this.data);
  }


  public clickRow(item) {
    this.clickRowData.emit(item);
  }

  
}
