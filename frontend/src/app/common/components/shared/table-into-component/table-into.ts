import { Component,  Input, EventEmitter, Output } from '@angular/core';

@Component({
  selector: 'vdi-table-into',
  templateUrl: './table-into.html',
  styleUrls: ['./table-into.scss']
})
export class TableIntoComponent  {

  @Input() item: {};
  @Input() collection: object[] = [];
  @Output() action: EventEmitter<object> = new EventEmitter<object>();

  constructor() {}

  public actionEditField(method) {
    this.action.emit(method);
  }

  ngOnInit() {
    console.log(this.item, this.collection);
  }

}
